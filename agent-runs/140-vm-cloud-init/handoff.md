# Handoff: box1-docs#140 VM cloud-init (NoCloud)

## Work completed

- **Workstream:** golden-path 03, cloud-init NoCloud for per-instance VM identity.
- **Slice:** the whole prompt up to review. Live acceptance is not done.
- **Repositories, branches and PRs:**
  - box1-templates `golden-path/140-cloud-init` @ `390cd79`, [PR #34](https://github.com/box1-org/box1-templates/pull/34);
  - box1-docs `golden-path/140-cloud-init-runbook`, [PR #147](https://github.com/box1-org/box1-docs/pull/147).
- **Changed paths:**
  - `templates/rhel-image-vm/{template.yaml, skeleton/Containerfile, skeleton/README.md, skeleton/{% if values.cloudInit === true %}rootfs-cloud-init{% endif %}/**}`;
  - `scripts/validate.mjs` and `README.md` in box1-templates;
  - `scripts/vm-cloud-init/*`, `runbooks/vm-cloud-init-identity.md` and `agent-runs/140-vm-cloud-init/**` in box1-docs.

## Tests and deployment proof

- Template checks:
  - `npm run validate`: pass.
  - `VM_BASELINE_REF=origin/main npm run validate`: pass. With the parameter off, the render is byte-identical to main `5663eb3`.
  - `npm run test:onboarding`: 57/57.
- Script tests: `python3 -I scripts/vm-cloud-init/test_assemble_cloud_init_secret.py -v`, 16/16.
- No image, digest, GitOps PR, deployment or boot. All live checks are in `test-plan/README.md`.

## Contract state

- **Template parameter:** `cloudInit` (boolean, default `false`), passed only to `fetchApplication`. The GitOps bundle is unchanged, so `validateVmBundle` is unchanged.
- **Instance bundle for #138:**
  - VM disk and volume `cloudinitdisk`, with `cloudInitNoCloud.secretRef.name: <instance>-cloud-init`.
  - ConfigMap `<instance>-site`, labelled `box1.org/instance: <instance>`. Keys: `siteId`, `keycloakClientId` and `keycloakTokenUrl` (required); `assetServiceUrl`, `kafkaBootstrapServers` and `otlpEndpoint` (optional).
  - The Secret `<instance>-cloud-init` (key `userdata`, labels `box1.org/instance` and `box1.org/cloud-init: userdata`) is created outside Git by the script.
- **Validator rules for #139:** listed in the runbook, plus "refuse `firmware.serial` starting with `ds=`".
- **Guest contract:**
  - `/etc/box1/site.env`: 0644 root.
  - `/etc/box1/credentials/keycloak-client-secret`: 0400 `box1-site`.
  - Service user `box1-site`.

## Operations and safety

- No credential appears in source, tests (fake values only), logs or evidence. The Secret is created only by an operator with approval.
- Writing the cloud-init Secret gives root in the guest. Only the script should write it.
- **Rollback:** revert box1-templates#34. No existing repository adopted the change.

## Next agent session

- **Next slice:** the approved live test plan, then #138 and #139 consume the spec.
- **Files to read:** `checkpoint.md`, `test-plan/README.md`, `runbooks/vm-cloud-init-identity.md`.
- **Blockers:**
  - approvals: onboarding `cloudinit-check`, the `cloudinit-test` namespace, a box1-ci RoleBinding, placeholder Secrets and VM deletion;
  - #131 for real Keycloak clients;
  - a confirmed service user name from #126.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#140
current_phase: 5 Review complete; waiting on owner approval for 6/7
repositories:
  - name: box1-org/box1-templates
    branch: golden-path/140-cloud-init
    commit: 390cd7949ca724b4e9c4947918a4e85ca30a1ba7
  - name: box1-org/box1-docs
    branch: golden-path/140-cloud-init-runbook
    commit: see PR #147 head
run_state_path: agent-runs/140-vm-cloud-init/
requirements:
  proposed: 1
  implemented: 5
  locally_tested: 2
  ci_verified: 0
  deployed: 0
  live_verified: 0
  blocked: 0
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [security]
open_decisions: [approve live test plan, confirm box1-site user name]
rollback_state: nothing merged or applied
next_action: owner merges box1-templates#34 then box1-docs#147 (about 10 s apart), then approves test-plan steps
```
