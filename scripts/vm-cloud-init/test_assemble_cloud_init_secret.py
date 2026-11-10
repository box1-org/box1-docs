#!/usr/bin/env python3
"""Offline tests for assemble_cloud_init_secret.py (box1-docs#140).

Run: python3 -I scripts/vm-cloud-init/test_assemble_cloud_init_secret.py -v

No cluster is contacted. Each test uses a freshly generated fake client secret and a
fake `oc` that records its arguments and stdin. Every test checks that the secret (and
its base64 forms) never reaches stdout, stderr or a command line.
"""

import base64
import json
import os
import secrets
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "assemble_cloud_init_secret.py")

FAKE_OC = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    log = os.environ["FAKE_OC_LOG"]
    stdin = sys.stdin.read() if "-f" in sys.argv else ""
    with open(log, "a") as f:
        f.write(json.dumps({"argv": sys.argv[1:], "stdin": stdin, "env_has_secret": "SITE_SECRET" in os.environ}) + "\\n")
    if sys.argv[1:3] == ["get", "configmap"]:
        sys.stdout.write(open(os.environ["FAKE_OC_CONFIGMAP"]).read())
        sys.exit(0)
    if sys.argv[1] == "apply":
        if os.environ.get("FAKE_OC_FAIL_ECHO"):
            # A failing oc that echoes what it was given must still not leak the credential.
            sys.stderr.write("error: rejected " + stdin + "\\n")
            sys.exit(1)
        dry = " (server dry run)" if "--dry-run=server" in sys.argv else ""
        sys.stdout.write("secret/" + json.loads(stdin)["metadata"]["name"] + " serverside-applied" + dry + "\\n")
        sys.exit(0)
    sys.exit(3)
    """)


def site_configmap(**overrides):
    cm = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "site-west-site",
            "namespace": "site-west-dev",
            "labels": {"box1.org/instance": "site-west", "backstage.io/kubernetes-id": "site-west"},
            "annotations": {"argocd.argoproj.io/tracking-id": "site-west:/ConfigMap:site-west-dev/site-west-site"},
        },
        "data": {
            "siteId": "site_ds9",
            "keycloakClientId": "site-west",
            "keycloakTokenUrl": "https://keycloak.example.test/realms/box1/protocol/openid-connect/token",
            "assetServiceUrl": "https://asset-service.example.test",
            "kafkaBootstrapServers": "box1-kafka-bootstrap.kafka.svc:9093",
            "otlpEndpoint": "http://box1-collector.observability.svc:4318",
        },
    }
    for key, value in overrides.items():
        if key == "data":
            cm["data"] = value
        elif key == "metadata":
            cm["metadata"].update(value)
        else:
            cm[key] = value
    return cm


class AssembleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.secret = "fake-" + secrets.token_urlsafe(32)
        self.secret_file = self.write("client-secret", self.secret + "\n", 0o600)
        self.oc = self.write("oc", FAKE_OC, 0o700)
        self.log = os.path.join(self.dir, "oc.log")
        self.cm_file = self.write_cm(site_configmap())

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text, mode):
        path = os.path.join(self.dir, name)
        with open(path, "w") as f:
            f.write(text)
        os.chmod(path, mode)
        return path

    def write_cm(self, cm, name="site-west-site.json"):
        return self.write(name, json.dumps(cm), 0o644)

    def run_script(self, *args, env=None, cm_file=None):
        full_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "FAKE_OC_LOG": self.log,
                    "FAKE_OC_CONFIGMAP": cm_file or self.cm_file}
        full_env.update(env or {})
        proc = subprocess.run([sys.executable, "-I", SCRIPT, "--oc", self.oc, *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=full_env)
        out, err = proc.stdout.decode(), proc.stderr.decode()
        for forbidden in self.forbidden():
            self.assertNotIn(forbidden, out, "credential leaked to stdout")
            self.assertNotIn(forbidden, err, "credential leaked to stderr")
        for call in self.oc_calls():
            for forbidden in self.forbidden():
                self.assertNotIn(forbidden, " ".join(call["argv"]), "credential on a command line")
        return proc.returncode, out, err

    def forbidden(self):
        return [self.secret, base64.b64encode(self.secret.encode()).decode()]

    def oc_calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as f:
            return [json.loads(line) for line in f]

    def applied_userdata(self):
        applies = [c for c in self.oc_calls() if c["argv"][0] == "apply"]
        self.assertEqual(len(applies), 1)
        manifest = json.loads(applies[0]["stdin"])
        return applies[0], manifest, base64.b64decode(manifest["data"]["userdata"]).decode()

    @staticmethod
    def cloud_config(userdata):
        lines = userdata.splitlines(True)
        assert lines[0] == "#cloud-config\n", lines[0]
        return json.loads("".join(l for l in lines if not l.startswith("#")))

    # --- plan (default) -------------------------------------------------------------

    def test_plan_reads_configmap_from_file_and_redacts_credential(self):
        code, out, err = self.run_script("--instance", "site-west", "--site-configmap-file", self.cm_file,
                                         "--client-secret-file", self.secret_file)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.oc_calls(), [], "plan mode must not call oc")
        self.assertIn("BOX1_SITE_ID=site_ds9", out)
        self.assertIn("BOX1_KEYCLOAK_CLIENT_SECRET_FILE=/etc/box1/credentials/keycloak-client-secret", out)
        self.assertIn("<redacted>", out)
        self.assertIn('"name": "site-west-cloud-init"', out)
        self.assertIn("bytes, not shown", out)
        self.assertIn("Would run (manifest on stdin): %s apply --server-side --force-conflicts --field-manager=box1-cloud-init-assembler -f -" % self.oc, out)
        self.assertNotIn("warning", err)

    def test_plan_reads_configmap_from_cluster_read_only(self):
        code, out, err = self.run_script("--instance", "site-west", "--client-secret-file", self.secret_file)
        self.assertEqual(code, 0, err)
        self.assertEqual([c["argv"] for c in self.oc_calls()],
                         [["get", "configmap", "site-west-site", "-n", "site-west-dev", "-o", "json"]])

    def test_untracked_configmap_is_refused_unless_allowed(self):
        cm = site_configmap()
        del cm["metadata"]["annotations"]
        cm_file = self.write_cm(cm)
        code, _, err = self.run_script("--instance", "site-west", "--site-configmap-file", cm_file,
                                       "--client-secret-file", self.secret_file, "--apply")
        self.assertEqual(code, 2)
        self.assertIn("no Argo CD tracking annotation", err)
        self.assertEqual(self.oc_calls(), [])
        code, _, err = self.run_script("--instance", "site-west", "--site-configmap-file", cm_file,
                                       "--client-secret-file", self.secret_file, "--allow-untracked", "--apply")
        self.assertEqual(code, 0, err)
        self.assertIn("not tracked by Argo CD", err)

    # --- apply ----------------------------------------------------------------------

    def test_apply_sends_secret_only_on_stdin(self):
        code, out, err = self.run_script("--instance", "site-west", "--client-secret-file", self.secret_file, "--apply")
        self.assertEqual(code, 0, err)
        self.assertIn("secret/site-west-cloud-init serverside-applied", out)
        call, manifest, userdata = self.applied_userdata()
        self.assertEqual(call["argv"], ["apply", "--server-side", "--force-conflicts", "--field-manager=box1-cloud-init-assembler", "-f", "-"])
        self.assertEqual(manifest["metadata"]["name"], "site-west-cloud-init")
        self.assertEqual(manifest["metadata"]["namespace"], "site-west-dev")
        self.assertEqual(manifest["metadata"]["labels"], {"box1.org/instance": "site-west", "box1.org/cloud-init": "userdata"})
        self.assertNotIn("app.kubernetes.io/instance", manifest["metadata"]["labels"], "must not look Argo-tracked")
        self.assertEqual(manifest["type"], "Opaque")
        self.assertEqual(list(manifest["data"]), ["userdata"])
        self.assertNotIn("stringData", manifest)
        for annotation in manifest["metadata"]["annotations"].values():
            self.assertNotIn(self.secret, annotation)

        cfg = self.cloud_config(userdata)
        self.assertEqual(list(cfg), ["write_files"], "user-data may only write files")
        site_env, credential = cfg["write_files"]
        self.assertEqual(site_env["path"], "/etc/box1/site.env")
        self.assertEqual((site_env["owner"], site_env["permissions"]), ("root:root", "0644"))
        self.assertEqual(site_env["content"], textwrap.dedent("""\
            BOX1_INSTANCE=site-west
            BOX1_SITE_ID=site_ds9
            BOX1_KEYCLOAK_CLIENT_ID=site-west
            BOX1_KEYCLOAK_TOKEN_URL=https://keycloak.example.test/realms/box1/protocol/openid-connect/token
            BOX1_ASSET_SERVICE_URL=https://asset-service.example.test
            BOX1_KAFKA_BOOTSTRAP_SERVERS=box1-kafka-bootstrap.kafka.svc:9093
            BOX1_OTLP_ENDPOINT=http://box1-collector.observability.svc:4318
            BOX1_KEYCLOAK_CLIENT_SECRET_FILE=/etc/box1/credentials/keycloak-client-secret
            """))
        self.assertNotIn(self.secret, site_env["content"])
        self.assertEqual(credential["path"], "/etc/box1/credentials/keycloak-client-secret")
        self.assertEqual((credential["owner"], credential["permissions"], credential["encoding"]),
                         ("box1-site:box1-site", "0400", "b64"))
        self.assertNotIn("defer", credential)
        self.assertEqual(base64.b64decode(credential["content"]).decode(), self.secret,
                         "credential file holds exactly the secret, without a trailing newline")

    def test_secret_from_environment_and_identical_output(self):
        self.run_script("--instance", "site-west", "--client-secret-file", self.secret_file, "--apply")
        _, first, _ = self.applied_userdata()
        os.remove(self.log)
        code, _, err = self.run_script("--instance", "site-west", "--client-secret-env", "SITE_SECRET", "--apply",
                                       env={"SITE_SECRET": self.secret})
        self.assertEqual(code, 0, err)
        self.assertFalse(any(c["env_has_secret"] for c in self.oc_calls()), "the secret variable must not reach oc")
        _, second, _ = self.applied_userdata()
        self.assertEqual(first, second, "the Secret is a pure function of the ConfigMap and the credential")

    def test_two_instances_share_nothing_but_the_shape(self):
        east = site_configmap(data={"siteId": "site_spacedock", "keycloakClientId": "site-east",
                                    "keycloakTokenUrl": "https://keycloak.example.test/realms/box1/protocol/openid-connect/token"},
                              metadata={"name": "site-east-site", "namespace": "site-east-dev",
                                        "labels": {"box1.org/instance": "site-east"}})
        code, _, err = self.run_script("--instance", "site-east", "--client-secret-file", self.secret_file, "--apply",
                                       cm_file=self.write_cm(east, "east.json"))
        self.assertEqual(code, 0, err)
        _, manifest, userdata = self.applied_userdata()
        self.assertEqual((manifest["metadata"]["name"], manifest["metadata"]["namespace"]), ("site-east-cloud-init", "site-east-dev"))
        self.assertIn("BOX1_SITE_ID=site_spacedock\n", self.cloud_config(userdata)["write_files"][0]["content"])
        self.assertNotIn("BOX1_ASSET_SERVICE_URL", userdata, "optional keys stay out when absent")

    def test_server_dry_run(self):
        code, out, err = self.run_script("--instance", "site-west", "--client-secret-file", self.secret_file, "--server-dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("(server dry run)", out)
        call, _, _ = self.applied_userdata()
        self.assertIn("--dry-run=server", call["argv"])

    def test_failing_oc_output_is_scrubbed(self):
        code, _, err = self.run_script("--instance", "site-west", "--client-secret-file", self.secret_file, "--apply",
                                       env={"FAKE_OC_FAIL_ECHO": "1"})
        self.assertEqual(code, 1)
        self.assertIn("<redacted>", err)

    # --- refusals -------------------------------------------------------------------

    def refused(self, cm=None, args=(), secret_text=None, secret_mode=0o600, message=""):
        secret_file = self.secret_file
        if secret_text is not None:
            secret_file = self.write("other-secret", secret_text, secret_mode)
        elif secret_mode != 0o600:
            os.chmod(secret_file, secret_mode)
        argv = list(args) or ["--instance", "site-west"]
        if "--client-secret-env" not in argv and "--client-secret-file" not in argv:
            argv += ["--client-secret-file", secret_file]
        cm_file = self.write_cm(cm, "refused.json") if cm is not None else self.cm_file
        code, out, err = self.run_script(*argv, "--site-configmap-file", cm_file, "--apply")
        self.assertEqual(code, 2, (out, err))
        self.assertIn(message, err)
        self.assertFalse(any(c["argv"][0] == "apply" for c in self.oc_calls()), "nothing may be applied")
        return err

    def test_refuses_credential_keys_in_configmap(self):
        for key in ["keycloakClientSecret", "password", "clientSecret"]:
            data = dict(site_configmap()["data"], **{key: "fake-not-allowed"})
            self.refused(site_configmap(data=data), message="outside the allowlist")

    def test_refuses_missing_required_keys(self):
        for key in ["siteId", "keycloakClientId", "keycloakTokenUrl"]:
            data = dict(site_configmap()["data"])
            del data[key]
            self.refused(site_configmap(data=data), message="missing " + key)

    def test_refuses_unsafe_values(self):
        base = site_configmap()["data"]
        for key, value in [("keycloakTokenUrl", "http://keycloak.example.test/token"),
                           ("keycloakTokenUrl", "https://user:pw@keycloak.example.test/token"),
                           ("assetServiceUrl", "https://asset.example.test/?token=abc"),
                           ("assetServiceUrl", "https://asset.example.test/$(id)"),
                           ("siteId", "site ds9"), ("siteId", "Site_DS9"), ("siteId", "site_ds9\nBOX1_X=1"),
                           ("otlpEndpoint", "http://collector:4318/'x'"),
                           ("kafkaBootstrapServers", "kafka:9093;rm"), ("keycloakClientId", 7)]:
            self.refused(site_configmap(data=dict(base, **{key: value})), message="invalid value")

    def test_refuses_wrong_configmap_identity(self):
        self.refused(site_configmap(metadata={"name": "site-east-site"}), message="expected ConfigMap site-west-site")
        self.refused(site_configmap(metadata={"namespace": "default"}), message="not site-west-dev")
        self.refused(site_configmap(metadata={"labels": {"box1.org/instance": "site-east"}}), message="box1.org/instance")
        self.refused(site_configmap(binaryData={"x": "AA=="}), message="binaryData")
        self.refused(site_configmap(kind="Secret"), message="expected ConfigMap")

    def test_refuses_bad_secret_sources(self):
        self.refused(secret_mode=0o644, message="readable by group or others")
        self.refused(secret_text="", message="empty")
        self.refused(secret_text="\n", message="empty")
        self.refused(secret_text="two words", message="single line")
        self.refused(secret_text="line1\nline2", message="single line")
        self.refused(secret_text="x" * 4097, message="longer than")
        self.refused(secret_text="café", message="printable ASCII")
        self.refused(args=["--instance", "site-west", "--client-secret-env", "UNSET_FOR_TEST"], message="is not set")
        link = os.path.join(self.dir, "link-to-secret")
        os.symlink(self.secret_file, link)
        self.refused(args=["--instance", "site-west", "--client-secret-file", link], message="symlinks are refused")
        self.refused(args=["--instance", "site-west", "--client-secret-file", os.path.join(self.dir, "missing")], message="cannot open")

    def test_refuses_unreadable_or_malformed_configmap_cleanly(self):
        code, _, err = self.run_script("--instance", "site-west", "--site-configmap-file", os.path.join(self.dir, "nope.json"),
                                       "--client-secret-file", self.secret_file)
        self.assertEqual(code, 2)
        self.assertIn("cannot read --site-configmap-file", err)
        self.assertNotIn("Traceback", err)
        self.refused(site_configmap(data=["siteId"]), message="must be a mapping")
        self.refused(site_configmap(metadata={"labels": None}), message="box1.org/instance")

    def test_refuses_bad_instance_names(self):
        for name in ["Site-West", "a", "site_west", "-x", "x" * 41, "../etc"]:
            self.refused(args=["--instance", name], message="--instance")

    def test_requires_exactly_one_secret_source(self):
        proc = subprocess.run([sys.executable, "-I", SCRIPT, "--instance", "site-west"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)
        proc = subprocess.run([sys.executable, "-I", SCRIPT, "--instance", "site-west", "--client-secret-file", self.secret_file,
                               "--client-secret-env", "X"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
