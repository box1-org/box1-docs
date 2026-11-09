# Golden path 05 — `vm-instance` profile and template (one OS image, many VMs)

> **This is a golden-path change, not a new service.** It makes "add a site" self-service: each run of a new template creates one more VM that boots an already-built, already-gated OS image. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Each instance needs about 2 vCPU, 4 GiB of RAM and a 20 GiB root disk. This is an estimate, not a measurement. Check LVMS headroom before provisioning.
- Onboarding, Secret creation, VM deletion and decommissioning need approval.
- The user merges. Wait about 10 seconds between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not touch `legacy-erp`, `vm-golden-check` or other VMs.
- Do not use Chrome.

**Issue:** [box1-docs#138](https://github.com/box1-org/box1-docs/issues/138), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies:** all are required before live acceptance.
- [#136](https://github.com/box1-org/box1-docs/issues/136) (`01_onboarding_profile_dispatch.md`): the handler table, released.
- [#139](https://github.com/box1-org/box1-docs/issues/139) (`02_gitops_vm_instance_validate_promote.md`): the validator rule and the promote target, merged.
- [#140](https://github.com/box1-org/box1-docs/issues/140) (`03_vm_cloud_init_nocloud.md`): the instance bundle specification, the assembly script and a cloud-init-enabled image.
- A `site-gateway-os` image with an approved `-disk` digest, from #126. Without it, use a throwaway cloud-init-enabled source image, which needs approval, or stop.

Staged rollout across instances is [#141](https://github.com/box1-org/box1-docs/issues/141) and is not part of this prompt.

## Mission

Add a `vm-instance` Developer Hub template and onboarding profile. One run creates one GitOps-only VM instance: its own namespace, its own identity (through cloud-init) and its own approved digest, booting the shared disk of an existing source image repository. There is no source repository and no build. Then create `site-west` (fixture site `site_ds9`) and `site-east` (fixture site `site_spacedock`) from Developer Hub.

## Verified baseline (observed 2026-11-08; verify before relying)

**One VM repo produces exactly one VM.** Everything below assumes the VM is named after its repository and boots `box1-ci/<repo>-disk`:

- `validateVmBundle` (`box1-templates/plugins/box1-onboarding/workflow.cjs` L106–163)
- `check_vm` (`box1-gitops/.../gitops-validate.yaml` L87, L110–114)
- `gitops-promote` (`name` is the repo, the workload directory and the Application)
- `bootc-channel`, `bootc-disk`
- `vm-smoke` and `bootc-apply`, which use `application-name` as the VM name

#139 lifts this for validation and promotion.

**The VM golden path** (`templates/rhel-image-vm`, template 1.0.0, plugin profile `virtual-machine`)
- Bundle files:
  - `namespace`, labelled `box1.org/workload-profile: virtual-machine`
  - `updater` (SA `<name>-updater` and an empty token Secret)
  - `admin-access` (SSH public key Secret)
  - `virtualmachine` (starts `Halted` with zero-digest annotations; volumes `root`, `serviceca`, `regtoken`; `accessCredentials` for `cloud-user`)
  - `datavolume` (`<name>-root`, `pullMethod: node`, `lvms-vg1`; added to the kustomization on first promotion)
  - `onboarding` (PaC Repository, the image-puller RoleBinding in `box1-ci` for Group `system:serviceaccounts:<ns>`, and observer Roles)
  - `applications/<name>.yaml`
- `vmVerify` (L590–611) waits for DataVolume `Succeeded`, VM `Ready`, VMI `AgentConnected`, Argo Synced/Healthy, and the `os-image-digest` annotation. It does **not** check the booted digest.
- `vm-smoke.yaml` L2–4 also states that it "checks what was approved, not what is booted".
- Booted-digest proof today comes from `bootc status` in the guest:
  - `bootc-apply.yaml` uses `virtctl ssh` as `box1-deploy`.
  - The 2026-11-05 VM achievement (`box1-docs/achievements/2026/2026-11-05-rhdh-vm-golden-path.md`) used SSH as `cloud-user`.

**Plugin inputs**
- `index.cjs` requires `name` and a 40-hex `sourceRevision` for every non-repository action.
- `box1:repository:ensure` creates a source repository; an instance has none.

**Decommissioning**
- `box1-docs/runbooks/service-decommission.md` (updated 2026-11-08) covers services only. It never mentions a VM, DataVolume or root PVC, the `<name>-disk` ImageStream, channel tags, the image-puller RoleBinding in `box1-ci`, or the updater SA and token.
- The parent `workloads-dev` Application has no prune. The runbook's finalizer steps (L34–40, L52–55) still apply.

**Capacity:** see the [2026-11-06 PV capacity audit](https://github.com/box1-org/box1-docs/blob/main/achievements/2026/2026-11-06-pv-capacity-audit.md).

## Decided design

This comes from the issue, together with the owner decisions recorded on #139 and #140.

**Template (`templates/vm-instance`)**
- Inputs:
  - instance name;
  - source image repository (must be on #139's allowlist; for example `site-gateway-os`);
  - `siteId` and endpoints, for the `<instance>-site` ConfigMap;
  - admin SSH public key;
  - CPU, memory and root-disk choices, as in `rhel-image-vm`.
- The template creates **no** source repository and skips `box1:repository:ensure`.
- Decide the `sourceRevision` semantics: the source repository's currently approved revision, read from its workload's `box1.org/source-revision`. Record this.
- Every onboarding step passes `profile: vm-instance`.

**GitOps bundle (`box1-workloads-dev/workloads/<instance>/`)**
- Namespace `<instance>-dev`, labelled `box1.org/workload-profile: vm-instance`.
- A VirtualMachine named after the instance:
  - annotation `box1.org/source-image: <source>`, using #139's name;
  - `os-image-digest` and `source-revision` annotations;
  - the `cloudinitdisk` volume with `cloudInitNoCloud.secretRef: <instance>-cloud-init`, as #140 specifies;
  - `serviceca` and `regtoken` disks;
  - `accessCredentials`.
- DataVolume `<instance>-root` from `box1-ci/<source>-disk@sha256:<source's approved disk digest>`.
- ConfigMap `<instance>-site`.
- Updater and admin-access resources, as in the VM golden path.
- `onboarding.yaml` with the image-puller RoleBinding and observer Roles, and **no** PaC Repository, because there is no source repository.
- `applications/<instance>.yaml`.

**Profile handlers (in the #136 table)**
- **Bundle validation:** mirrors #139's `check_vm_instance`.
- **Build barrier:** none.
- **Platform checks:**
  - namespace, updater SA and puller binding;
  - the `<instance>-cloud-init` Secret exists. If it doesn't, report a clear "create it with the #140 runbook" message and keep the VM Halted.
- **Build:** none. Record the source's approved image and disk digests as this instance's digests.
- **Promote:** first promotion through #139's `vm-instance` target. It updates **only this instance's** `os-image-digest` annotation and DataVolume digest.
- **Verify:**
  - VM `Ready`, `AgentConnected`, Argo Synced/Healthy;
  - **the booted digest equals the approved digest.** Choose and record the mechanism:
    - `virtctl ssh … bootc status --json`, with a deploy key and RBAC like `legacy-erp`'s `deploy-access.yaml`;
    - guest-agent exec, if available;
    - or a guest heartbeat that reports the booted digest.
- **Catalog:**
  - registers a Component (or Resource) for the instance, linked to the source;
  - the completion predicate does not need a source repository.

**Release tracking (owner decision on #139)**
- Instances **pin digests only**. They never follow the source's `:development` channel tag.
- Day-2 promotion of one instance leaves the others unchanged.

**"Add a site"**
- Running the template again creates another site.
- Before an instance can start, the out-of-Git cloud-init Secret must be assembled with the #140 runbook. This is the only manual step.

## Scope and guardrails

**In scope**
- In `box1-templates`: the template, the profile entry and handlers, `catalog-info.yaml` Location, `scripts/validate.mjs` and tests.
- In `box1-docs`: the decommission runbook updated for `virtual-machine` and `vm-instance`.
- The two site instances, created through Developer Hub.

**Out of scope**
- #139's validator and promote changes.
- #140's image work.
- `site-gateway-os` creation.
- Staged rollout (#141).
- The site NetworkPolicy (#126).

**Plugin release:** follow the #136 process.

**Updating the decommission runbook for instances**
- Delete the VM, DataVolume and root PVC, the `<instance>-cloud-init` Secret, the site ConfigMap, the puller RoleBinding in `box1-ci`, and the Hub status record and Lease.
- **Never** delete the source's `<source>-disk` or `<source>` ImageStreams or tags while other instances or the source use them.
- Record whether any data PVC is `Prune=false`.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #138 only with the evidence named.

- [ ] Two instances created from Developer Hub boot the same `site-gateway-os` digest, each in its own namespace with its own identity.
  - Evidence: Hub task IDs (no manual `oc` except the approved Secret bootstrap), the two namespaces, `bootc status` digests from both guests, and `/etc/box1/site.env` showing `site_ds9` and `site_spacedock`.
- [ ] Promoting a new digest to one instance leaves the other instance's digest unchanged.
  - Evidence: the promotion PR's file list (one instance only), then both VMs' annotations and booted digests after the merge.
  - Needs a second approved source digest, which can be a trivial rebuild.
- [ ] Deleting an instance follows the [service decommission runbook](https://github.com/box1-org/box1-docs/blob/main/runbooks/service-decommission.md), updated for the instance profile, and does not affect the source image or other instances.
  - Evidence: the runbook PR, then a third throwaway instance created and decommissioned (approval needed), with the source ImageStreams and the other instances checked before and after.
- [ ] `rhel-image-vm` onboarding still passes its regression run.
  - Evidence: a regression VM onboarded on the new plugin digest, then decommissioned with the updated runbook.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/138-vm-instance/`.

**Discovery must cover**
- The released #136, #139 and #140 contracts: the handler interface, promote params, allowlist, bundle specification and runbook.
- The source image's approved digests.
- LVMS free capacity and node CPU and memory headroom.
- The fixture site IDs in `box1-ops-contracts`.
- The guest-access options for booted-digest checks.
- Any active onboarding.

**Design decisions to record**
- `sourceRevision` semantics.
- The booted-digest mechanism.
- The catalog entity kind.
- Instance sizing.
- The plugin version.
- The order of creating `site-east` and `site-west`.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 0 Discovery | All three dependencies delivered; capacity headroom recorded |
| 3 Implementation | Template renders; `service`, `virtual-machine` and `artifact` renders unchanged |
| 6 Delivery | Plugin pinned; Hub synced; both instances reconciled by Argo |
| 7 Live acceptance | All four criteria, with evidence |

**Verification scenarios**
- The cloud-init Secret is missing: the instance stays Halted with a clear message.
- The source is not on the allowlist: rejected.
- The instance name collides with an existing workload: rejected.
- A second run with the same name resumes, not duplicates.
- Promoting one instance leaves the other unchanged.
- The source releases a new digest: instances unchanged until promoted.
- An instance is deleted: the source and the other instance are unaffected.
- The `rhel-image-vm` regression passes.

**Stop conditions**
- A dependency is not delivered.
- Capacity is insufficient.
- There is no approved source digest.
- No booted-digest mechanism exists without a new credential, and none is approved.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the template and profile;
- the two instances, with namespaces, digests and identities;
- the promotion evidence;
- the runbook PR;
- the measured resource use of each VM, which feeds #126;
- the rollback for each instance (revert its promotion PR, or decommission it).

Tick the completed items on #138. Name what #141 needs from this profile.
