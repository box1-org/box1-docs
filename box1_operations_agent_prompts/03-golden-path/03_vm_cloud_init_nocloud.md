# Golden path 03 — VM cloud-init (NoCloud) for per-instance identity

> **Golden-path change, not a new service.** This adds cloud-init to the RHEL image-mode VM golden path, so one OS image can boot as several identities. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety:**
- No credential value goes in Git, VM manifests, logs, evidence or handoffs. That includes the Keycloak client secret.
- Creating or rotating a Secret requires approval. Document how to provision it and never record its value.
- The user merges. Wait about 10 s between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not touch `legacy-erp` or `vm-golden-check`.
- Do not use Chrome.

**Issue:** [box1-docs#140](https://github.com/box1-org/box1-docs/issues/140), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies:**
- It can run in parallel with #136 and #139.
- Agree the validator rule with #139 (`02_gitops_vm_instance_validate_promote.md`).
- #138 (`05_vm_instance_profile_template.md`) consumes the bundle shape defined here.
- The per-site Keycloak client comes from [#131](https://github.com/box1-org/box1-docs/issues/131). If #131 has not provided one, use a placeholder test client, which needs approval, or stop.

## Mission

Give each VM instance its own non-secret configuration (`siteId`, endpoints) and its machine credential, while every instance boots one shared bootc image digest. The mechanism is cloud-init with the NoCloud datasource, and the credentials are passed by reference only. Existing VMs must keep booting unchanged.

## Verified baseline

Observed 2026-11-08 on `box1-templates` main `5663eb3` and `box1-gitops` main `4bcc907`. Verify before relying on it.

- **There is no cloud-init anywhere.** A grep of `box1-templates` for `cloud-init`, `cloudinit`, `nocloud` and `cloudInit` finds nothing. No VirtualMachine in `box1-workloads-dev` has a cloud-init volume.
- **`templates/rhel-image-vm/skeleton/Containerfile`:**
  - `FROM registry.redhat.io/rhel10/rhel-bootc:10.2@sha256:…`;
  - installs only `qemu-guest-agent ${{ values.extraPackages }}`, using build-time entitlement secrets;
  - copies `rootfs/`;
  - enables `box1-registry-setup.service`;
  - **disables `bootc-fetch-apply-updates.timer`**;
  - sets `<name>.target` as the default target;
  - ends with `bootc container lint`.
- **How the guest gets its inputs today** (`templates/rhel-image-vm/gitops/workloads/<name>/virtualmachine.yaml`):
  - SSH keys arrive through `accessCredentials` and qemu-guest-agent for `cloud-user`, from Secret `<name>-admin-ssh`, which holds public keys only.
  - The service CA and the registry token arrive as serial disks `serviceca` and `regtoken`. `rootfs/usr/libexec/box1/registry-setup` reads them, puts the token on tmpfs at `/run/ostree/auth.json`, and skips a missing disk.
  - `bootc-disk.yaml` builds the qcow2 with only `cloud-user`.
- **Validators reject a cloud-init Secret.**
  - `box1-gitops/platform/pipelines/tasks/gitops-validate.yaml` L98–104 allows only SSH public-key Secrets and the empty token Secret.
  - The plugin's `validateVmBundle` (`plugins/box1-onboarding/workflow.cjs` L106–163) requires exactly the volumes `regtoken, root, serviceca`, exactly two Secrets, and a fixed resource list.
  - `scripts/validate.mjs` L240–247 checks the Containerfile and the rootfs file list.
- **There is no secret manager** (no ExternalSecrets, Vault or SealedSecrets). Secrets are created by hand, outside Git. Precedents:
  - `box1-docs/runbooks/rhdh-onboarding-plugin-oci.md`, for the registry pull Secret;
  - `kafka-postgres-foundation.md` in earlier docs, for the `replace-before-sync` placeholder;
  - comments in `box1-gitops/platform/pipelines/ci/bootc-build.yaml`.
- **Existing VMs are separate repositories generated from the template.** `legacy-erp` and `vm-golden-check` keep their own Containerfiles. A template change reaches them only if their repositories adopt it.

## Decided design

The owner decided on 2026-11-08 to use cloud-init with NoCloud rather than more serial disks. The assembly decision is recorded on #140.

**Image** (`rhel-image-vm` template)
- Install `cloud-init` and pin `datasource_list: [ NoCloud, None ]` in `/etc/cloud/cloud.cfg.d/`, so the guest never probes network metadata services.
- Keep qemu-guest-agent SSH propagation as the admin-key path. cloud-init must not manage `cloud-user`'s keys or password: set `ssh_pwauth: false`, and disable `users` and `ssh` key modules where they would conflict.
- Make cloud-init a template parameter (proposed `cloudInit`, default `false`). Repositories that are generated from the template without it stay byte-identical. Record the decision if you make it the default instead.
- Prove that an image *with* cloud-init boots normally *without* a NoCloud disk, for example as `vm-golden-check` does.
- Confirm cloud-init coexists with:
  - the bootc `/etc` three-way merge across upgrades;
  - the disabled `bootc-fetch-apply-updates.timer`;
  - `box1-registry-setup.service` ordering;
  - qemu-guest-agent `accessCredentials`.

**Instance bundle** (consumed by #138)
- The VirtualMachine adds a disk and volume `cloudinitdisk` with `cloudInitNoCloud.secretRef.name: <instance>-cloud-init`. Inline `userData` is never allowed.
- Git holds a non-secret ConfigMap `<instance>-site` with `siteId` and endpoints.
- **The `<instance>-cloud-init` Secret is assembled outside Git** (owner decision). A documented script, stored in `box1-docs` with a runbook:
  1. reads the `<instance>-site` ConfigMap;
  2. reads the client secret from its source without printing it;
  3. renders `#cloud-config` userData. `write_files` writes `/etc/box1/site.env` (mode 0644) and the credential file (mode 0400, owned by the site service user, proposed path `/etc/box1/credentials/keycloak-client-secret`);
  4. applies the Secret with `oc apply`. This is an approved bootstrap step, not the deployment mechanism.
- The VM stays `Halted` until the Secret exists. The #138 platform checks fail clearly when it is missing.
- **Not taken:**
  - a hand-written Secret holding all of the userData, which would leave site identity invisible in Git;
  - more serial disks.

**Validator rule** (implemented with #139)
- No plaintext credentials in VirtualMachine manifests, userData or the site ConfigMap in Git.
- The cloud-init Secret must be referenced, never rendered from Git.

**Lifecycle documentation**
- cloud-init's per-instance semantics: what re-applies when the VM or its root disk is re-created (new instance-id), and what does not re-apply on reboot.
- How to rotate the credential: update the Secret, then restart or re-create the VM.
- The data disk is preserved and never managed by cloud-init.

## Scope and guardrails

**In scope:**
- `templates/rhel-image-vm` (Containerfile, rootfs, gitops skeleton, `template.yaml` parameter);
- `scripts/validate.mjs`;
- `validateVmBundle` changes, only if the template's own bundle changes when the parameter is on;
- the instance bundle *specification* for #138;
- the assembly script and runbook in `box1-docs`;
- the validator rule, coordinated with #139.

**Out of scope:**
- creating `site-gateway-os`, `site-west` or `site-east` (#126 and #138);
- Keycloak client creation (#131);
- changing `legacy-erp` or `vm-golden-check`.

**Test environment:**
- Run boot tests in a dedicated test namespace (needs approval) or locally with the template's `local/` build path, using a throwaway image.
- Put test materials and evidence in `box1-docs`.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #140 only with the evidence named.

- [ ] A `site-gateway-os` VM booted as `site-west` reads `siteId=site_ds9`, and as `site-east` reads `site_spacedock`, from the same image digest.
  - Before #138 lands, prove it with two test VMs from one cloud-init-enabled test image digest.
  - Record `bootc status` (digest) and `/etc/box1/site.env` from each guest.
  - Re-run on the real instances once #138 exists, or hand that re-run to #138 explicitly.
- [ ] No credential appears in Git or in VM manifests. The client secret is readable in the guest only by the site service user.
  - Evidence: a repository grep; the validator negative tests; `oc get vm -o yaml` showing only `secretRef`; and in the guest, `stat` of the credential file, a failed read as another user, and a successful read as the service user.
- [ ] Re-creating the VM re-applies identity without losing data on the data disk.
  - Delete and re-create the root disk or VM (needs approval).
  - Record a data-disk marker file before and after, and the identity after.
- [ ] Existing VMs (`legacy-erp`, `vm-golden-check`) keep booting unchanged.
  - Show that their manifests and images are untouched.
  - Show that an image built from the template with the parameter off is identical to before, using `npm run validate` rendered output.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/140-vm-cloud-init/`.

**Discovery must cover:**
- the installed OpenShift Virtualization version and the `cloudInitNoCloud` fields of its VirtualMachine CRD, including `secretRef` and `networkDataSecretRef`;
- the `cloud-init` package version available in RHEL 10 entitlement repositories;
- whether `rhel-bootc:10.2` already ships any cloud-init configuration;
- #131's state;
- the secret-handling precedents listed above.

**Design decisions to record:**
- default versus opt-in parameter;
- disabled cloud-init modules;
- credential path and owner;
- site service user name (coordinate with the `site-gateway` design in #126);
- assembly script interface;
- test namespace.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | CRD fields and package availability confirmed on the cluster, not assumed |
| 3 Implementation | Parameter-off rendering byte-identical to before |
| 4 Verification | Boot without a NoCloud disk; boot with two identities from one digest; re-create with data preserved; SSH through the guest agent still works |
| 5 Review | Security pass confirms no credential in Git, manifests, logs or evidence |
| 7 Live acceptance | The four acceptance items, with evidence, or an explicit handoff to #138 for the real-instance re-run |

**Verification scenarios:**
- Secret missing at start: the VM stays Halted, with a clear message;
- malformed userData;
- Secret rotated;
- bootc upgrade to a new digest keeps the identity;
- bootc rollback;
- guest agent SSH unaffected;
- `registry-setup` still installs the token and CA.

**Stop conditions:**
- the installed KubeVirt lacks `cloudInitNoCloud.secretRef`;
- cloud-init conflicts with bootc in a way that needs an image-design change;
- no Keycloak client is available and no placeholder is approved.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the template parameter and its rendered diff;
- the instance bundle specification for #138 (exact volumes, Secret and ConfigMap names, labels);
- the assembly script and runbook paths;
- the validator rule handed to #139;
- boot evidence;
- rollback: revert the template PR, which existing repositories never adopted.

Tick the completed items on #140.
