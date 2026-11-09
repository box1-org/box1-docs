#!/usr/bin/env python3
"""Assemble a VM instance's <instance>-cloud-init Secret outside Git (box1-docs#140).

The VM's site identity lives in Git as the non-secret ConfigMap <instance>-site. The
machine credential (the Keycloak client secret) never does. This script combines the
two into cloud-init NoCloud user-data and wraps it in the Secret that the VirtualMachine
references through cloudInitNoCloud.secretRef. The guest's cloud-init writes:

  /etc/box1/site.env                            0644 root:root          site settings
  /etc/box1/credentials/keycloak-client-secret  0400 box1-site:box1-site machine credential

By default the script only prints a plan: the user-data with the credential redacted,
the Secret metadata, and the `oc apply` it would run. --server-dry-run asks the API
server to validate the Secret without storing it; --apply stores it. The credential is
read from a file or an environment variable, travels to `oc` only on stdin, and is
never printed, logged, written to disk or passed on a command line.

Runbook: runbooks/vm-cloud-init-identity.md. Tests: test_assemble_cloud_init_secret.py.
Python 3.9+, standard library only.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

FIELD_MANAGER = "box1-cloud-init-assembler"
SERVICE_USER = "box1-site"
SITE_ENV_PATH = "/etc/box1/site.env"
CREDENTIAL_PATH = "/etc/box1/credentials/keycloak-client-secret"
USERDATA_KEY = "userdata"  # KubeVirt reads "userdata" (or "userData") from the Secret
INSTANCE_LABEL = "box1.org/instance"
MAX_SECRET_LENGTH = 4096

INSTANCE_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
# site.env must stay safe for systemd EnvironmentFile= and for `. site.env`: values carry
# no quotes, spaces, `$`, `;`, `&`, user info (`@`) or query strings (`?`).
_PATH = r"(?:/[A-Za-z0-9._~%+:-]*)*"
HTTPS_URL_RE = re.compile(r"https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?" + _PATH)
HTTP_URL_RE = re.compile(r"https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?" + _PATH)
HOST_PORTS_RE = re.compile(r"[A-Za-z0-9.-]+:[0-9]{1,5}(?:,[A-Za-z0-9.-]+:[0-9]{1,5})*")
SECRET_RE = re.compile(r"[\x21-\x7e]+")  # printable ASCII, no whitespace

# ConfigMap <instance>-site data keys -> (site.env variable, required, value pattern).
# Only these keys are accepted: anything else, including a credential, is refused.
SITE_KEYS = {
    "siteId": ("BOX1_SITE_ID", True, re.compile(r"[a-z][a-z0-9_]{1,62}")),
    "keycloakClientId": ("BOX1_KEYCLOAK_CLIENT_ID", True, re.compile(r"[a-z][a-z0-9-]{1,62}")),
    "keycloakTokenUrl": ("BOX1_KEYCLOAK_TOKEN_URL", True, HTTPS_URL_RE),
    "assetServiceUrl": ("BOX1_ASSET_SERVICE_URL", False, HTTPS_URL_RE),
    "kafkaBootstrapServers": ("BOX1_KAFKA_BOOTSTRAP_SERVERS", False, HOST_PORTS_RE),
    "otlpEndpoint": ("BOX1_OTLP_ENDPOINT", False, HTTP_URL_RE),
}


class UsageError(Exception):
    """A refused input. Messages never contain the credential."""


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Assemble the <instance>-cloud-init Secret from the <instance>-site ConfigMap "
        "and a client secret. Prints a redacted plan unless --server-dry-run or --apply is given.")
    p.add_argument("--instance", required=True, help="VM instance name, e.g. site-west")
    p.add_argument("--namespace", help="namespace (default: <instance>-dev)")
    p.add_argument("--site-configmap-file", metavar="PATH",
                   help="read the ConfigMap from this JSON file (e.g. `oc get configmap -o json`) "
                        "instead of the cluster")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--client-secret-file", metavar="PATH",
                        help="file holding only the client secret; must not be readable by group or others")
    source.add_argument("--client-secret-env", metavar="NAME",
                        help="environment variable holding the client secret")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--server-dry-run", action="store_true",
                      help="validate the Secret on the API server without storing it")
    mode.add_argument("--apply", action="store_true", help="create or update the Secret")
    p.add_argument("--oc", default=os.environ.get("OC", "oc"), help="oc binary (default: $OC or oc)")
    args = p.parse_args(argv)
    if not INSTANCE_RE.fullmatch(args.instance) or not 3 <= len(args.instance) <= 40:
        raise UsageError("--instance must be a DNS label of 3-40 characters, e.g. site-west")
    args.namespace = args.namespace or args.instance + "-dev"
    if not INSTANCE_RE.fullmatch(args.namespace) or len(args.namespace) > 63:
        raise UsageError("--namespace must be a DNS label")
    return args


def read_secret(args):
    if args.client_secret_file:
        try:
            st = os.stat(args.client_secret_file)
        except OSError as e:
            raise UsageError("cannot read --client-secret-file: %s" % e.strerror)
        if not stat.S_ISREG(st.st_mode):
            raise UsageError("--client-secret-file must be a regular file")
        if st.st_mode & 0o077:
            raise UsageError("--client-secret-file is readable by group or others; chmod 600 it first")
        with open(args.client_secret_file, "rb") as f:
            raw = f.read(MAX_SECRET_LENGTH + 3)
        try:
            value = raw.decode("ascii")
        except UnicodeDecodeError:
            raise UsageError("the client secret must be printable ASCII")
    else:
        if args.client_secret_env not in os.environ:
            raise UsageError("environment variable %s is not set" % args.client_secret_env)
        value = os.environ[args.client_secret_env]
    # Tolerate one trailing newline from `echo` or an editor; nothing else.
    if value.endswith("\r\n"):
        value = value[:-2]
    elif value.endswith("\n"):
        value = value[:-1]
    if not value:
        raise UsageError("the client secret is empty")
    if len(value) > MAX_SECRET_LENGTH:
        raise UsageError("the client secret is longer than %d characters" % MAX_SECRET_LENGTH)
    if not SECRET_RE.fullmatch(value):
        raise UsageError("the client secret must be a single line of printable ASCII without spaces")
    return value


def read_configmap(args):
    name = args.instance + "-site"
    if args.site_configmap_file:
        with open(args.site_configmap_file, encoding="utf-8") as f:
            text = f.read()
    else:
        proc = subprocess.run([args.oc, "get", "configmap", name, "-n", args.namespace, "-o", "json"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise UsageError("could not read ConfigMap %s/%s: %s"
                             % (args.namespace, name, proc.stderr.decode("utf-8", "replace").strip()))
        text = proc.stdout.decode("utf-8")
    try:
        cm = json.loads(text)
    except ValueError:
        raise UsageError("the ConfigMap must be JSON (oc get configmap %s -o json)" % name)
    return cm


def site_settings(cm, instance, namespace):
    """Validate the <instance>-site ConfigMap and return the ordered site.env pairs."""
    name = instance + "-site"
    meta = cm.get("metadata") or {}
    if cm.get("kind") != "ConfigMap" or meta.get("name") != name:
        raise UsageError("expected ConfigMap %s" % name)
    if meta.get("namespace", namespace) != namespace:
        raise UsageError("ConfigMap %s is in namespace %s, not %s" % (name, meta.get("namespace"), namespace))
    if (meta.get("labels") or {}).get(INSTANCE_LABEL) != instance:
        raise UsageError("ConfigMap %s must carry the label %s: %s" % (name, INSTANCE_LABEL, instance))
    if cm.get("binaryData"):
        raise UsageError("ConfigMap %s must not have binaryData" % name)
    data = cm.get("data") or {}
    unknown = sorted(set(data) - set(SITE_KEYS))
    if unknown:
        raise UsageError("ConfigMap %s has keys outside the allowlist (%s): %s. Credentials never go in "
                         "the ConfigMap." % (name, ", ".join(SITE_KEYS), ", ".join(unknown)))
    pairs = [("BOX1_INSTANCE", instance)]
    for key, (env, required, pattern) in SITE_KEYS.items():
        if key not in data:
            if required:
                raise UsageError("ConfigMap %s is missing %s" % (name, key))
            continue
        value = data[key]
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise UsageError("ConfigMap %s: %s has an invalid value (no user info, query string, "
                             "spaces or quotes are allowed)" % (name, key))
        pairs.append((env, value))
    pairs.append(("BOX1_KEYCLOAK_CLIENT_SECRET_FILE", CREDENTIAL_PATH))
    tracked = "argocd.argoproj.io/tracking-id" in (meta.get("annotations") or {})
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return pairs, digest, tracked


def render_userdata(instance, namespace, pairs, digest, secret):
    """#cloud-config user-data. The body is JSON, which is valid YAML for cloud-init."""
    site_env = "".join("%s=%s\n" % kv for kv in pairs)
    config = {
        "write_files": [
            {"path": SITE_ENV_PATH, "owner": "root:root", "permissions": "0644", "content": site_env},
            {"path": CREDENTIAL_PATH, "owner": "%s:%s" % (SERVICE_USER, SERVICE_USER), "permissions": "0400",
             "encoding": "b64", "content": base64.b64encode(secret.encode("ascii")).decode("ascii")},
        ],
    }
    header = ("#cloud-config\n"
              "# %s/%s: assembled by box1-docs scripts/vm-cloud-init/assemble_cloud_init_secret.py\n"
              "# from ConfigMap %s-site (data sha256 %s). Not stored in Git.\n"
              % (namespace, instance, instance, digest))
    return header + json.dumps(config, indent=2) + "\n"


def secret_manifest(instance, namespace, digest, userdata):
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "metadata": {
            "name": instance + "-cloud-init",
            "namespace": namespace,
            "labels": {INSTANCE_LABEL: instance, "box1.org/cloud-init": "userdata"},
            "annotations": {
                "box1.org/site-config-sha256": digest,
                "box1.org/assembled-by": "box1-docs/scripts/vm-cloud-init/assemble_cloud_init_secret.py",
            },
        },
        "data": {USERDATA_KEY: base64.b64encode(userdata.encode("utf-8")).decode("ascii")},
    }


def scrubber(secret, userdata):
    forbidden = [secret, base64.b64encode(secret.encode()).decode(), base64.b64encode(userdata.encode()).decode()]

    def scrub(text):
        for value in forbidden:
            text = text.replace(value, "<redacted>")
        return text
    return scrub


def oc_apply_command(args, dry_run):
    cmd = [args.oc, "apply", "--server-side", "--field-manager=" + FIELD_MANAGER, "-f", "-"]
    if dry_run:
        cmd.insert(2, "--dry-run=server")
    return cmd


def main(argv=None):
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        secret = read_secret(args)
        pairs, digest, tracked = site_settings(read_configmap(args), args.instance, args.namespace)
    except UsageError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    userdata = render_userdata(args.instance, args.namespace, pairs, digest, secret)
    manifest = secret_manifest(args.instance, args.namespace, digest, userdata)
    scrub = scrubber(secret, userdata)
    if not tracked:
        print("warning: ConfigMap %s-site has no Argo CD tracking annotation; site settings should come "
              "from Git (box1-workloads-dev)" % args.instance, file=sys.stderr)

    if not (args.apply or args.server_dry_run):
        shown = dict(manifest, data={USERDATA_KEY: "<%d bytes, not shown>" % len(manifest["data"][USERDATA_KEY])})
        print("# Plan only: nothing was sent to the cluster. Add --server-dry-run or --apply.")
        print("# user-data (credential redacted):")
        print(scrub(userdata), end="")
        print("# Secret:")
        print(json.dumps(shown, indent=2))
        print("# Would run (manifest on stdin): %s" % " ".join(oc_apply_command(args, False)))
        return 0

    cmd = oc_apply_command(args, args.server_dry_run)
    print("# Running (manifest on stdin, not shown): %s" % " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, input=json.dumps(manifest).encode("utf-8"),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sys.stdout.write(scrub(proc.stdout.decode("utf-8", "replace")))
    sys.stderr.write(scrub(proc.stderr.decode("utf-8", "replace")))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
