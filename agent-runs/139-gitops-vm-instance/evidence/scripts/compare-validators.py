#!/usr/bin/env python3
"""Compare box1-gitops-validate outcomes before and after a change (box1-docs#139).

usage: compare-validators.py OLD_TASK_YAML NEW_TASK_YAML WORKLOADS_DEV_GIT_DIR REV...
For each box1-workloads-dev revision, renders every workloads/*/ with kubectl
kustomize and records (profile or failure message, printed PASS line) under the
old and new embedded scripts. Prints one line per revision and exits non-zero on
any difference. Read-only: uses `git archive` into a temp dir.
"""
import io, pathlib, shutil, subprocess, sys, tarfile, tempfile

def load(task):
    text = pathlib.Path(task).read_text()
    start = text.index("    script: |")
    body = []
    for line in text[start:].splitlines()[1:]:
        if line and not line.startswith("      "):
            break
        body.append(line[6:] if line else "")
    ns = {"__name__": "validator"}
    exec(compile("\n".join(body), task, "exec"), ns)
    return ns

def old_pass(profile, name):
    if profile == "virtual-machine":
        return "PASS: Kustomize, VirtualMachine, pinned OS and disk digests, update disks: " + name
    return "PASS: Kustomize, resources, probes, immutable image: " + name

def outcome(v, name, rendered, new):
    try:
        profile = v["validate"](name, rendered)
    except AssertionError as error:
        return ("FAIL", str(error))
    return (profile, v["PASS_MESSAGES"][profile] + name if new else old_pass(profile, name))

old, new = load(sys.argv[1]), load(sys.argv[2])
repo = sys.argv[3]
kubectl = shutil.which("kubectl")
differences = 0
for rev in sys.argv[4:]:
    with tempfile.TemporaryDirectory() as tmp:
        data = subprocess.check_output(["git", "-C", repo, "archive", rev])
        tarfile.open(fileobj=io.BytesIO(data)).extractall(tmp)
        root = pathlib.Path(tmp)
        targets = sorted((root / "workloads").glob("*/kustomization.yaml"))
        results = []
        for target in targets:
            rendered = subprocess.check_output([kubectl, "kustomize", str(target.parent)], text=True)
            a, b = outcome(old, target.parent.name, rendered, False), outcome(new, target.parent.name, rendered, True)
            results.append((target.parent.name, a[0]))
            if a != b:
                differences += 1
                print("DIFF", rev, target.parent.name, a, b)
        ci = new["validation_targets"](root)[1]
        summary = ", ".join("%s=%s" % r for r in results)
        print("%s: %d workloads identical old/new; ci bundles=%d; %s" % (rev[:12], len(targets), len(ci), summary))
sys.exit(1 if differences else 0)
