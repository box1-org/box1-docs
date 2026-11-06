"""Dump Box1 manually-created objects, strip live state, redact secrets.

Usage: python dump.py <output-dir>
Reads from the current oc context (read-only).
"""
import json, os, re, subprocess, sys
import yaml

OUT = sys.argv[1]
SENSITIVE_ENV = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE|CREDENTIAL)", re.I)

DROP_META = {"uid", "resourceVersion", "generation", "creationTimestamp", "managedFields",
             "selfLink", "ownerReferences", "finalizers", "generateName", "deletionGracePeriodSeconds"}
DROP_LABEL_PREFIX = ("operators.coreos.com/", "olm.", "pod-security.kubernetes.io/",
                     "openshift-pipelines.tekton.dev/", "kubernetes.io/metadata.name",
                     "security.openshift.io/", "controller.cert-manager.io/", "pod-template-hash",
                     "machineconfiguration.openshift.io/managed")
DROP_ANNO_PREFIX = ("kubectl.kubernetes.io/", "deployment.kubernetes.io/", "openshift.io/sa.scc.",
                    "security.openshift.io/", "olm.", "openshift.io/generated-by",
                    "openshift.io/host.generated", "pv.kubernetes.io/", "volume.kubernetes.io/",
                    "volume.beta.kubernetes.io/", "include.release.openshift.io/",
                    "release.openshift.io/", "capability.openshift.io/", "cert-manager.io/",
                    "argocd.argoproj.io/", "operatorframework.io/", "image.openshift.io/",
                    "openshift.io/image.dockerRepositoryCheck",  "oauth-apiserver.openshift.io/", "config.openshift.io/",
                    "machineconfiguration.openshift.io/", "operator.openshift.io/")


def oc_json(args):
    r = subprocess.run(["oc", "get", *args, "-o", "json"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"oc get {' '.join(args)} failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def filt(d, prefixes):
    if not d:
        return None
    out = {k: v for k, v in d.items() if not k.startswith(prefixes)}
    return out or None


def redact_env(containers):
    for c in containers or []:
        for e in c.get("env", []) or []:
            if "value" in e and SENSITIVE_ENV.search(e["name"]):
                e["value"] = "<REDACTED>"


def clean(o):
    o.pop("status", None)
    m = o["metadata"]
    host_generated = (m.get("annotations") or {}).get("openshift.io/host.generated") == "true"
    for k in list(m):
        if k in DROP_META:
            del m[k]
    for key, pref in (("labels", DROP_LABEL_PREFIX), ("annotations", DROP_ANNO_PREFIX)):
        v = filt(m.get(key), pref)
        if v:
            m[key] = v
        else:
            m.pop(key, None)
    kind = o["kind"]
    spec = o.get("spec") or {}
    if kind == "Namespace":
        o.pop("spec", None)
    elif kind in ("Deployment", "StatefulSet", "DaemonSet"):
        tmeta = spec["template"].get("metadata", {})
        tmeta.pop("creationTimestamp", None)
        ann = filt(tmeta.get("annotations"), ("kubectl.kubernetes.io/restartedAt", "openshift.io/"))
        if ann:
            tmeta["annotations"] = ann
        else:
            tmeta.pop("annotations", None)
        ps = spec["template"]["spec"]
        redact_env(ps.get("containers"))
        redact_env(ps.get("initContainers"))
    elif kind == "Service":
        for k in ("clusterIP", "clusterIPs", "ipFamilies", "ipFamilyPolicy", "internalTrafficPolicy"):
            spec.pop(k, None)
    elif kind == "Route" and host_generated:
        spec.pop("host", None)
    elif kind == "PersistentVolumeClaim":
        spec.pop("volumeName", None)
    elif kind == "ImageStream":
        for t in spec.get("tags", []) or []:
            t.pop("generation", None)
    elif kind == "ServiceAccount":
        o.pop("secrets", None)
        o.pop("imagePullSecrets", None)
    elif kind == "BuildConfig":
        for t in spec.get("triggers", []) or []:
            for wk in ("github", "generic", "gitlab", "bitbucket"):
                if isinstance(t.get(wk), dict) and "secret" in t[wk]:
                    t[wk]["secret"] = "<REDACTED>"
    elif kind == "Secret":
        keys = sorted(set((o.get("data") or {}).keys()) | set((o.get("stringData") or {}).keys()))
        o.pop("data", None)
        o["stringData"] = {k: "<REDACTED: supply value out of band>" for k in keys}
    return o


def write(rel, objs):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("# Cleaned export from the Box1 cluster (status and live metadata removed).\n")
        if rel.startswith("secrets/"):
            f.write("# WARNING: REDACTED TEMPLATE. Values are placeholders. Do NOT apply as-is:\n"
                    "# applying this file overwrites the live Secret with placeholder text.\n"
                    "# Fill every value from the secure source first (see ../README.md).\n")
        yaml.safe_dump_all(objs, f, sort_keys=False, default_flow_style=False, width=100)
    print(f"{rel}: {', '.join(o['kind'] + '/' + o['metadata']['name'] for o in objs)}")


def get(kind, name, ns=None):
    args = [kind, name] + (["-n", ns] if ns else [])
    return clean(oc_json(args))


def operator_bundle(ns, sub, include_ns=True):
    objs = []
    if include_ns:
        objs.append(get("namespace", ns))
        for og in oc_json(["operatorgroups.operators.coreos.com", "-n", ns])["items"]:
            objs.append(clean(og))
    objs.append(get("subscriptions.operators.coreos.com", sub, ns))
    return objs


OPERATORS = [
    ("openshift-gitops-operator", "openshift-gitops-operator", "openshift-gitops-operator", True),
    ("cert-manager", "cert-manager-operator", "openshift-cert-manager-operator", True),
    ("nvidia-gpu", "nvidia-gpu-operator", "gpu-operator-certified", True),
    ("node-feature-discovery", "openshift-nfd", "nfd", True),
    ("kernel-module-management", "openshift-kmm", "kernel-module-management", True),
    ("web-terminal", "openshift-operators", "web-terminal", False),
    ("lvm-storage", "openshift-lvm-storage", "lvms-operator", True),
    ("odf", "openshift-storage", "odf-operator", True),
    ("lightspeed", "openshift-lightspeed", "lightspeed-operator", True),
    ("openshift-virtualization", "openshift-cnv", "kubevirt-hyperconverged", True),
]
for fname, ns, sub, inc in OPERATORS:
    write(f"operators/{fname}.yaml", operator_bundle(ns, sub, inc))

write("operators/catalogsources.yaml", [
    get("catalogsources.operators.coreos.com", n, "openshift-marketplace")
    for n in ("redhat-operators-v422", "certified-operators-v422")])

write("operands/nvidia-gpu-clusterpolicy.yaml", [get("clusterpolicies.nvidia.com", "gpu-cluster-policy")])
write("operands/nfd-instance.yaml", [get("nodefeaturediscoveries.nfd.openshift.io", "nfd-instance", "openshift-nfd")])
write("operands/lvmcluster.yaml", [get("lvmclusters.lvm.topolvm.io", "box1-storage", "openshift-lvm-storage")])
write("operands/odf-storagecluster.yaml", [get("storageclusters.ocs.openshift.io", "ocs-storagecluster", "openshift-storage")])
write("operands/hyperconverged.yaml", [get("hyperconvergeds.hco.kubevirt.io", "kubevirt-hyperconverged", "openshift-cnv")])

write("cluster-config/kubeletconfig-box1-pod-density.yaml", [get("kubeletconfig", "box1-pod-density")])
write("cluster-config/machineconfigs.yaml", [get("machineconfig", n) for n in ("10-ipmi-modules", "11-i2c-core-builtin-override")])
write("cluster-config/cert-manager-issuer-and-certificates.yaml", [
    get("clusterissuers.cert-manager.io", "letsencrypt-production"),
    get("certificates.cert-manager.io", "openshift-api", "openshift-config"),
    get("certificates.cert-manager.io", "openshift-apps", "openshift-ingress")])
write("cluster-config/oauth.yaml", [get("oauth.config.openshift.io", "cluster")])
write("cluster-config/apiserver.yaml", [get("apiserver.config.openshift.io", "cluster")])
write("cluster-config/ingresscontroller-default.yaml", [get("ingresscontroller.operator.openshift.io", "default", "openshift-ingress-operator")])

ns = "agent-sandbox-system"
write("workloads/agent-sandbox.yaml", [
    get("namespace", ns),
    get("crd", "sandboxes.agents.x-k8s.io"),
    get("serviceaccount", "agent-sandbox-controller", ns),
    get("clusterrole", "agent-sandbox-controller"),
    get("clusterrolebinding", "agent-sandbox-controller"),
    get("service", "agent-sandbox-controller", ns),
    get("deployment", "agent-sandbox-controller", ns)])
write("workloads/vllm-test.yaml", [
    get("namespace", "vllm"),
    get("pvc", "vllm-models-cache", "vllm"),
    get("deployment", "vllm-test", "vllm"),
    get("service", "vllm-frontend", "vllm"),
    get("service", "vllm-test-2", "vllm"),
    get("route", "route-purple-bass", "vllm")])
write("workloads/inventory-poc.yaml", [
    get("namespace", "inventory-poc"),
    get("imagestream", "inventory", "inventory-poc"),
    get("imagestream", "inventory-image", "inventory-poc"),
    get("buildconfig", "inventory", "inventory-poc"),
    get("deployment", "inventory-deployment", "inventory-poc"),
    get("service", "inventory-service", "inventory-poc"),
    get("route", "inventory-route", "inventory-poc")])

SECRETS = {
    "cert-manager": ["cloudflare-api-token"],
    "openshift-config": ["htpasswd-xtglx"],
    "openshift-devspaces": ["github-oauth-config"],
    "openshift-pipelines": ["pipelines-as-code-secret"],
    "keycloak": ["keycloak-db-secret", "openshell-mike-initial-login"],
    "rhdh": ["developer-hub-db", "developer-hub-secrets", "developer-hub-platform-secrets",
             "dynamic-plugins-registry-auth"],
    "stackrox": ["acs-oidc-config", "admission-control-tls", "collector-tls", "sensor-tls",
                 "tls-cert-admission-control", "tls-cert-collector", "tls-cert-sensor"],
    "vllm": ["admission-control-tls", "collector-tls", "sensor-tls"],
    "box1-ci": ["rhacs-ci", "rhtpa-ci", "redhat-registry-pull", "legacy-erp-deploy-ssh",
                "etc-pki-entitlement"],
    "asset-service-dev": ["asset-service-postgres"],
    "fulfillment-adapter-dev": ["fulfillment-adapter-postgres"],
    "trusted-profile-analyzer": ["rhtpa-ci", "rhtpa-database"],
    "openshell": ["openshell-credential-storage-key-encryption-key", "openshell-jwt-keys"],
}
for sns, names in SECRETS.items():
    write(f"secrets/{sns}.yaml", [get("secret", n, sns) for n in names])
