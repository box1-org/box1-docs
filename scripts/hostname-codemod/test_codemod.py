"""Unit tests: python3 -m unittest -v (from this directory)."""
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codemod  # noqa: E402

GIT = codemod.GitRule({"from_org": "box1-org", "to_base": "https://gitlab.example.com/box1-org"})
DOM = codemod.DomainRule({"from": "apps.ocp.box1.org", "to": "apps.new.example.com"})
REG = codemod.RegistryRule({"from": "image-registry.openshift-image-registry.svc:5000/box1-ci/", "to": "quay.io/box1/"})


def run(rule, text):
    stats, notes = Counter(), []
    return rule.apply(text, stats, notes), stats


class GitRuleTest(unittest.TestCase):
    def test_repo_urls(self):
        self.assertEqual(run(GIT, "https://github.com/box1-org/order-service")[0],
                         "https://gitlab.example.com/box1-org/order-service")
        self.assertEqual(run(GIT, "url: https://github.com/box1-org/order-service.git\n")[0],
                         "url: https://gitlab.example.com/box1-org/order-service.git\n")

    def test_tree_blob_commit_get_dash(self):
        self.assertEqual(run(GIT, "url:https://github.com/box1-org/x/tree/main/")[0],
                         "url:https://gitlab.example.com/box1-org/x/-/tree/main/")
        self.assertEqual(run(GIT, "[a](https://github.com/box1-org/x/blob/main/README.md)")[0],
                         "[a](https://gitlab.example.com/box1-org/x/-/blob/main/README.md)")
        self.assertEqual(run(GIT, "https://github.com/box1-org/x/commit/abc123")[0],
                         "https://gitlab.example.com/box1-org/x/-/commit/abc123")

    def test_github_only_links_kept(self):
        for t in ("https://github.com/box1-org/box1-docs/issues/164",
                  "https://github.com/box1-org/x/pull/7", "https://github.com/box1-org/x/releases"):
            out, stats = run(GIT, t)
            self.assertEqual(out, t)
            self.assertTrue(any("kept" in k for k in stats))

    def test_raw_and_slug(self):
        self.assertEqual(run(GIT, "https://raw.githubusercontent.com/box1-org/x/main/a/b.yaml")[0],
                         "https://gitlab.example.com/box1-org/x/-/raw/main/a/b.yaml")
        self.assertEqual(run(GIT, "    github.com/project-slug: box1-org/order-service\n")[0],
                         "    gitlab.com/project-slug: box1-org/order-service\n")

    def test_scheme_less_and_other_orgs(self):
        self.assertEqual(run(GIT, "see github.com/box1-org/x for details")[0],
                         "see gitlab.example.com/box1-org/x for details")
        self.assertEqual(run(GIT, "https://github.com/other-org/x")[0], "https://github.com/other-org/x")
        self.assertEqual(run(GIT, "box1-org/box1-docs#164")[0], "box1-org/box1-docs#164")

    def test_keep_repos(self):
        g = codemod.GitRule({"from_org": "box1-org", "to_base": "https://g/box1-org", "keep_repos": ["box1-gitops"]})
        self.assertEqual(run(g, "https://github.com/box1-org/box1-gitops.git")[0],
                         "https://github.com/box1-org/box1-gitops.git")


class DomainRuleTest(unittest.TestCase):
    def test_suffix_and_boundaries(self):
        self.assertEqual(run(DOM, "host: order-service-dev.apps.ocp.box1.org")[0],
                         "host: order-service-dev.apps.new.example.com")
        self.assertEqual(run(DOM, "https://keycloak.apps.ocp.box1.org/auth/realms/box1")[0],
                         "https://keycloak.apps.new.example.com/auth/realms/box1")
        self.assertEqual(run(DOM, "*.apps.ocp.box1.org")[0], "*.apps.new.example.com")
        self.assertEqual(run(DOM, "xapps.ocp.box1.org")[0], "xapps.ocp.box1.org")

    def test_annotation_keys_untouched(self):
        t = "box1.org/source-revision: abc\nbox1.org/instance: site-east\n"
        self.assertEqual(run(DOM, t)[0], t)
        self.assertEqual(run(GIT, t)[0], t)


class RegistryRuleTest(unittest.TestCase):
    def test_prefix_and_digest(self):
        t = "newName: image-registry.openshift-image-registry.svc:5000/box1-ci/order-service\ndigest: sha256:ab"
        self.assertEqual(run(REG, t)[0], "newName: quay.io/box1/order-service\ndigest: sha256:ab")


class RepoRunTest(unittest.TestCase):
    def test_dry_run_excludes_and_rebuild_flag(self):
        with tempfile.TemporaryDirectory() as root:
            repo = os.path.join(root, "svc")
            os.makedirs(os.path.join(repo, "src/main/resources"))
            os.makedirs(os.path.join(repo, "docs"))
            files = {
                "catalog-info.yaml": "github.com/project-slug: box1-org/svc\n",
                "src/main/resources/application.properties": "quarkus.http.cors.origins=https://svc.apps.ocp.box1.org\n",
                "VERIFICATION.md": "https://svc.apps.ocp.box1.org\n",
                "docs/notes.md": "node quark.host.box1.org, api https://api.github.com/repos/x\n",
            }
            for rel, body in files.items():
                with open(os.path.join(repo, rel), "w") as f:
                    f.write(body)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            cfg = {"exclude_paths": ["**/VERIFICATION*.md"]}
            r = codemod.process_repo("svc", repo, cfg, [GIT, DOM], apply=False, diff_dir=None)
            self.assertEqual(sorted(r["files"]), ["catalog-info.yaml", "src/main/resources/application.properties"])
            self.assertEqual(r["image_inputs"], ["src/main/resources/application.properties"])
            self.assertIn("quark.host.box1.org", r["unmapped"])
            self.assertTrue(any("GitHub API" in k for k in r["manual"]))
            # dry run wrote nothing
            with open(os.path.join(repo, "catalog-info.yaml")) as f:
                self.assertIn("github.com/project-slug", f.read())


if __name__ == "__main__":
    unittest.main()
