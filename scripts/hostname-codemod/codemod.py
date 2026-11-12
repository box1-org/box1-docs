#!/usr/bin/env python3
"""Rewrite Box1 hostnames across repositories, from an explicit rule file.

Rule types (see example-config.json):
  git      github.com/<org>/<repo> URLs -> another Git host (GitLab URL shapes).
           Repository, .git, blob, tree, commit and raw links are rewritten.
           Pull request, issue, release, compare and actions links are KEPT:
           they only exist on GitHub (the mirror copies git refs, not PRs).
           Also rewrites Backstage github.com/project-slug annotations.
  domain   one DNS suffix -> another, on label boundaries
           (order-service-dev.apps.ocp.box1.org -> order-service-dev.<new>).
  registry an image repository prefix -> another (for example the internal
           registry -> quay.io/<org>/). Digests are never touched.

Never rewritten: box1.org/<key> annotation and label keys (they are not
hostnames), excluded repositories and paths (history and evidence).

Reported, not rewritten: api.github.com and codeload.github.com use (code
that calls the GitHub API needs a real port), and any *.box1.org host no
rule covers.

Usage:
  codemod.py --config rules.json --repos DIR [--apply] [--commit BRANCH] [--diff-dir DIR]
DIR holds one clone per repository (directory name = repository name).
Default is a dry run: nothing is written; a summary (and diffs with
--diff-dir) shows what would change. --apply writes files; --commit also
creates BRANCH and commits in each changed repository (no push).

Python 3.9+, standard library only.
"""

import argparse
import difflib
import fnmatch
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

TEXT_EXT = {".yaml", ".yml", ".json", ".md", ".adoc", ".txt", ".properties", ".java", ".py", ".js", ".ts",
            ".tsx", ".jsx", ".html", ".css", ".xml", ".toml", ".cfg", ".ini", ".sh", ".env", ".conf", ".tpl",
            ".j2", ".njk", ".cjs", ".mjs", ".kt", ".go", ".sql", ".csv", ".service", ".container", ".kube"}
TEXT_NAMES = {"Containerfile", "Dockerfile", "Makefile", "OWNERS", "CODEOWNERS", ".gitignore"}
# Files that end up inside an image: a change here means the image must be rebuilt.
IMAGE_INPUT_GLOBS = ["src/**", "*/src/**", "Containerfile", "*/Containerfile", "Dockerfile", "*/Dockerfile",
                     "pom.xml", "*/pom.xml", "package.json", "*/package.json", "*.py", "app/**", "*/app/**"]
URL_END = r"""[^\s"'<>)\]`,]*"""


def is_text(path):
    base = os.path.basename(path)
    return base in TEXT_NAMES or os.path.splitext(base)[1].lower() in TEXT_EXT


def glob_match(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) or (p.endswith("/**") and rel.startswith(p[:-3] + "/")) or
               (p.startswith("**/") and fnmatch.fnmatch(os.path.basename(rel), p[3:])) or
               (p.startswith("**/") and fnmatch.fnmatch(rel, p[3:])) or
               ("/**/" in p and fnmatch.fnmatch(rel, p.replace("/**/", "/*/")))
               for p in patterns)


# ---------------------------------------------------------------- rules
class GitRule:
    """github.com/<org>/<repo>... -> <to_base>/<repo>... in GitLab URL shapes."""

    KEEP = ("pull", "pulls", "issues", "releases", "compare", "actions", "discussions", "wiki", "settings",
            "security", "projects", "milestone", "milestones", "labels")

    def __init__(self, cfg):
        self.org = cfg["from_org"]
        self.to_base = cfg["to_base"].rstrip("/")          # https://gitlab.example.com/box1-org
        self.to_group = self.to_base.rsplit("/", 1)[1]
        self.slug_annotation = cfg.get("slug_annotation", "gitlab.com/project-slug")
        self.keep_repos = set(cfg.get("keep_repos", []))
        org = re.escape(self.org)
        self.url = re.compile(r"(?P<scheme>https?://)?(?<![\w.-])github\.com/" + org +
                              r"/(?P<repo>[A-Za-z0-9_.-]+?)(?P<git>\.git)?(?=$|[/\s\"'<>)\]`,#?])(?P<rest>/" +
                              URL_END + r")?")
        self.raw = re.compile(r"https?://raw\.githubusercontent\.com/" + org +
                              r"/(?P<repo>[A-Za-z0-9_.-]+)/(?P<rest>" + URL_END + ")")
        self.slug = re.compile(r"(?P<key>github\.com/project-slug)(?P<sep>\s*:\s*['\"]?)" + org + r"/")
        self.name = "git"

    def apply(self, text, stats, notes):
        def url(m):
            repo, rest = m.group("repo"), m.group("rest") or ""
            if repo in self.keep_repos:
                return m.group(0)
            seg = rest.split("/")[1] if rest else ""
            if seg in self.KEEP:
                stats["git: kept GitHub-only link (" + seg + ")"] += 1
                return m.group(0)
            if seg in ("blob", "tree", "commit", "raw", "blame", "commits"):
                rest = "/-" + rest
            elif seg:
                notes.append("unrecognised GitHub path kept: " + m.group(0)[:120])
                stats["git: unrecognised path kept"] += 1
                return m.group(0)
            stats["git: repository URL"] += 1
            # Keep scheme-less mentions scheme-less (github.com/org/repo -> host/group/repo).
            base = self.to_base if m.group("scheme") else self.to_base.split("://", 1)[-1]
            return base + "/" + repo + (m.group("git") or "") + rest

        def raw(m):
            if m.group("repo") in self.keep_repos:
                return m.group(0)
            ref_path = m.group("rest")
            if "/" not in ref_path:
                return m.group(0)
            ref, path = ref_path.split("/", 1)
            stats["git: raw URL"] += 1
            return "%s/%s/-/raw/%s/%s" % (self.to_base, m.group("repo"), ref, path)

        def slug(m):
            stats["git: project-slug annotation"] += 1
            return self.slug_annotation + m.group("sep") + self.to_group + "/"

        text = self.raw.sub(raw, text)
        text = self.slug.sub(slug, text)
        return self.url.sub(url, text)


class DomainRule:
    def __init__(self, cfg):
        self.src, self.dst = cfg["from"], cfg["to"]
        self.rx = re.compile(r"(?<![A-Za-z0-9-])" + re.escape(self.src) + r"(?![A-Za-z0-9-])")
        self.name = "domain " + self.src

    def apply(self, text, stats, notes):
        def sub(m):
            stats["domain: " + self.src] += 1
            return self.dst
        return self.rx.sub(sub, text)


class RegistryRule:
    def __init__(self, cfg):
        self.src, self.dst = cfg["from"], cfg["to"]
        self.name = "registry " + self.src

    def apply(self, text, stats, notes):
        n = text.count(self.src)
        if n:
            stats["registry: " + self.src] += n
        return text.replace(self.src, self.dst)


RULES = {"git": GitRule, "domain": DomainRule, "registry": RegistryRule}

REPORT = [
    ("GitHub API call (needs a code port, not a hostname)", re.compile(r"api\.github\.com")),
    ("codeload.github.com download", re.compile(r"codeload\.github\.com")),
]
HOST = re.compile(r"(?<![A-Za-z0-9.-])((?:[a-z0-9-]+\.)+box1\.org)(?![A-Za-z0-9-])")


# ---------------------------------------------------------------- run
def load(path):
    with open(path) as f:
        cfg = json.load(f)
    rules = [RULES[r["type"]](r) for r in cfg["rules"]]
    return cfg, rules


def git_files(repo_dir):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=repo_dir, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("%s: not a git clone (%s)" % (repo_dir, out.stderr.strip()))
    return [p for p in out.stdout.split("\0") if p]


def process_repo(name, repo_dir, cfg, rules, apply, diff_dir):
    excl = cfg.get("exclude_paths", [])
    mapped = [r.dst for r in rules if isinstance(r, DomainRule)] + [r.src for r in rules if isinstance(r, DomainRule)]
    stats, notes, manual, unmapped = Counter(), [], Counter(), Counter()
    changed, image_inputs = [], []
    diffs = []
    for rel in git_files(repo_dir):
        if glob_match(rel, excl) or not is_text(rel):
            continue
        path = os.path.join(repo_dir, rel)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        new = text
        for rule in rules:
            new = rule.apply(new, stats, notes)
        for label, rx in REPORT:
            for _ in rx.finditer(new):
                manual["%s: %s" % (label, rel)] += 1
        for m in HOST.finditer(new):
            host = m.group(1)
            if not any(host == d or host.endswith("." + d) for d in mapped):
                unmapped[host] += 1
        if new != text:
            changed.append(rel)
            if glob_match(rel, IMAGE_INPUT_GLOBS) and not rel.startswith((".tekton/", "deploy/")):
                image_inputs.append(rel)
            if diff_dir is not None:
                diffs.extend(difflib.unified_diff(text.splitlines(True), new.splitlines(True),
                                                  "a/" + rel, "b/" + rel))
            if apply:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
    if diff_dir is not None and diffs:
        os.makedirs(diff_dir, exist_ok=True)
        with open(os.path.join(diff_dir, name + ".diff"), "w") as f:
            f.writelines(diffs)
    return {"repo": name, "files": changed, "stats": stats, "notes": notes, "manual": manual,
            "unmapped": unmapped, "image_inputs": image_inputs}


def commit(repo_dir, branch, message):
    def git(*a):
        r = subprocess.run(["git", *a], cwd=repo_dir, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("git %s: %s" % (a[0], r.stderr.strip()))
        return r.stdout
    git("switch", "-c", branch)
    git("commit", "-q", "-am", message)
    return git("rev-parse", "--short", "HEAD").strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--repos", required=True, help="directory with one clone per repository")
    ap.add_argument("--only", nargs="*", help="limit to these repositories")
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    ap.add_argument("--commit", metavar="BRANCH", help="with --apply: create BRANCH and commit per repository")
    ap.add_argument("--diff-dir", help="write <repo>.diff files here")
    ap.add_argument("--json", help="write the full report as JSON here")
    a = ap.parse_args(argv)
    if a.commit and not a.apply:
        ap.error("--commit needs --apply")
    cfg, rules = load(a.config)
    skip = set(cfg.get("exclude_repos", []))
    names = sorted(d for d in os.listdir(a.repos) if os.path.isdir(os.path.join(a.repos, d, ".git")))
    if a.only:
        names = [n for n in names if n in a.only]
    results = []
    for name in names:
        if name in skip:
            print("%-24s excluded by config" % name)
            continue
        r = process_repo(name, os.path.join(a.repos, name), cfg, rules, a.apply, a.diff_dir)
        if a.commit and r["files"]:
            r["commit"] = commit(os.path.join(a.repos, name), a.commit, cfg.get("commit_message", "Update hostnames"))
        results.append(r)

    total = Counter()
    print("\n%-24s %5s %7s  %s" % ("repository", "files", "rebuild", "replacements"))
    for r in results:
        total.update(r["stats"])
        reps = ", ".join("%s=%d" % (k, v) for k, v in sorted(r["stats"].items()) if "kept" not in k)
        print("%-24s %5d %7s  %s" % (r["repo"], len(r["files"]), "YES" if r["image_inputs"] else "-", reps or "-"))
    print("\nTotals: " + ", ".join("%s=%d" % kv for kv in sorted(total.items())))
    rebuild = [r["repo"] for r in results if r["image_inputs"]]
    print("Repositories whose images must be rebuilt (changed image inputs): %s" % (", ".join(rebuild) or "none"))
    manual = [(r["repo"], k, v) for r in results for k, v in r["manual"].items()]
    if manual:
        print("\nManual follow-up (not rewritten):")
        for repo, k, v in manual:
            print("  %-22s %s (%d)" % (repo, k, v))
    unmapped = Counter()
    for r in results:
        unmapped.update(r["unmapped"])
    if unmapped:
        print("\n*.box1.org hosts no rule covers (left as is): " +
              ", ".join("%s (%d)" % kv for kv in unmapped.most_common()))
    notes = [(r["repo"], n) for r in results for n in r["notes"]]
    for repo, n in notes[:20]:
        print("  note %-17s %s" % (repo, n))
    if a.json:
        with open(a.json, "w") as f:
            json.dump([{**r, "stats": dict(r["stats"]), "manual": dict(r["manual"]), "unmapped": dict(r["unmapped"])}
                       for r in results], f, indent=2)
    print("\nMode: %s" % ("APPLIED" + (" and committed on " + a.commit if a.commit else "") if a.apply else
                          "dry run (nothing written)"))


if __name__ == "__main__":
    main()
