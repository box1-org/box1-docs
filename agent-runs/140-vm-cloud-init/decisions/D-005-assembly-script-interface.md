# D-005 Assembly script interface

`scripts/vm-cloud-init/assemble_cloud_init_secret.py` (Python 3.9+, standard library).

- `--instance NAME` (required), `--namespace` (default `<instance>-dev`).
- ConfigMap source: the cluster (`oc get configmap <instance>-site -o json`, read-only) or `--site-configmap-file`.
- Credential source (exactly one): `--client-secret-file` (regular file, owned by the caller, mode without group/other bits, no symlink) or `--client-secret-env` (never passed on to `oc`).
- Mode: plan by default (redacted user-data, Secret metadata, the command); `--server-dry-run`; `--apply` (`oc apply --server-side --force-conflicts --field-manager=box1-cloud-init-assembler -f -`, manifest on stdin).
- Refuses ConfigMap keys outside the allowlist, invalid values, a ConfigMap without an Argo CD tracking annotation (unless `--allow-untracked`, for test namespaces).
- Secret: `<instance>-cloud-init`, `Opaque`, key `userdata`, labels `box1.org/instance`, `box1.org/cloud-init: userdata`, annotation `box1.org/site-config-sha256` (ConfigMap data only). No Argo CD tracking label.
- User-data is `#cloud-config` followed by a JSON body (valid YAML), with only `write_files`.
