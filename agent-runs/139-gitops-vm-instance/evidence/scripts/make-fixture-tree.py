#!/usr/bin/env python3
"""Build a box1-workloads-dev tree with #139 fixtures added (box1-docs#139).

usage: make-fixture-tree.py GITOPS_TASKS_DIR SOURCE_TREE OUT_DIR [variant]
Copies SOURCE_TREE and adds workloads/site-west (promoted vm-instance) and
workloads/site-east (unbuilt vm-instance) of source site-gateway-os, plus
ci/site-gateway (artifact-profile PaC bundle), using the fixtures from
test-gitops-validate.py. variant: valid (default), wrong-vm-name, tag-disk,
inline-userdata, ci-deployment.
"""
import importlib.util, pathlib, shutil, sys, textwrap
tasks, source, out = map(pathlib.Path, sys.argv[1:4])
variant = sys.argv[4] if len(sys.argv) > 4 else "valid"
spec = importlib.util.spec_from_file_location("vt", tasks / "test-gitops-validate.py")
vt = importlib.util.module_from_spec(spec); spec.loader.exec_module(vt)
shutil.copytree(source, out, ignore=shutil.ignore_patterns(".git"))

def write(base, files):
    base.mkdir(parents=True)
    for path, content in files.items():
        (base / path).write_text(textwrap.dedent(content).lstrip())

_, west = vt.instance_bundle("site-west", promoted=True)
_, east = vt.instance_bundle("site-east")
_, ci = vt.ci_bundle("site-gateway")
if variant == "wrong-vm-name":
    west["virtualmachine.yaml"] = west["virtualmachine.yaml"].replace("  name: site-west\n", "  name: site-other\n")
elif variant == "tag-disk":
    west["datavolume.yaml"] = west["datavolume.yaml"].replace("site-gateway-os-disk@" + vt.DISK_DIGEST, "site-gateway-os-disk:latest")
elif variant == "inline-userdata":
    west["virtualmachine.yaml"] = west["virtualmachine.yaml"].replace(
        "                        secretRef:\n", "                        userData: '#cloud-config'\n                        secretRef:\n")
elif variant == "ci-deployment":
    ci["deployment.yaml"] = """
        apiVersion: apps/v1
        kind: Deployment
        metadata: {name: site-gateway, namespace: box1-ci}
        spec:
          selector: {matchLabels: {app: g}}
          template:
            metadata: {labels: {app: g}}
            spec: {containers: [{name: c, image: quay.io/x/y:1}]}
    """
    ci["kustomization.yaml"] += "  - deployment.yaml\n"
elif variant != "valid":
    raise SystemExit("unknown variant " + variant)
write(out / "workloads" / "site-west", west)
write(out / "workloads" / "site-east", east)
write(out / "ci" / "site-gateway", ci)
