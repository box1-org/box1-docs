#!/usr/bin/env python3
"""Run box1-gitops-validate's embedded script end to end, offline (box1-docs#139).

usage: run-validator-main.py TASK_YAML TREE_DIR
Executes the Task script as __main__ with urllib patched: the box1-workloads-dev
zipball is built from TREE_DIR and the pinned kubectl download is served from the
local kubectl (with a matching .sha256). No network or cluster access. The Task's
/tmp/gitops-validation work directory is redirected to $VALIDATION_ROOT, which
must not exist yet.
"""
import hashlib, io, os, pathlib, shutil, sys, urllib.request, zipfile

task, tree = sys.argv[1], pathlib.Path(sys.argv[2])
text = pathlib.Path(task).read_text()
start = text.index("    script: |")
body = []
for line in text[start:].splitlines()[1:]:
    if line and not line.startswith("      "):
        break
    body.append(line[6:] if line else "")

archive = io.BytesIO()
with zipfile.ZipFile(archive, "w") as z:
    for path in sorted(tree.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            z.write(path, "box1-org-box1-workloads-dev-fixture/" + str(path.relative_to(tree)))
kubectl = pathlib.Path(shutil.which("kubectl")).read_bytes()

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

def fake_urlopen(request, timeout=None):
    url = request if isinstance(request, str) else request.full_url
    if "/zipball/" in url: return Response(archive.getvalue())
    if url.endswith("kubectl.sha256"): return Response(hashlib.sha256(kubectl).hexdigest().encode())
    if url.endswith("/kubectl"): return Response(kubectl)
    raise AssertionError("unexpected URL " + url)

urllib.request.urlopen = fake_urlopen
os.environ.setdefault("REVISION", "f" * 40)
os.environ.setdefault("GITHUB_TOKEN", "unused-offline")
script = "\n".join(body)
assert script.count("'/tmp/gitops-validation'") == 1
script = script.replace("'/tmp/gitops-validation'", repr(os.environ["VALIDATION_ROOT"]))
exec(compile(script, task, "exec"), {"__name__": "__main__"})
