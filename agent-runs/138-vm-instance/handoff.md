# Handoff: box1-docs#138 `vm-instance` profile and template

## Work completed
- **Workstream:** golden path 05. The `vm-instance` template and onboarding profile, plus the #140 rules reconciled into the #139 validator.
- **Repositories, branches and PRs:**
  - box1-templates#36: `golden-path/138-vm-instance` → `golden-path/137-artifact-profile`, head `69f54c3`.
  - box1-gitops#134: `golden-path/138-vm-instance` → `golden-path/137-maven-bundle`, head `2030fcb`.
  - box1-docs: `agent-run/138-vm-instance` → `main` (this PR).
- **Template and profile:**
  - `templates/vm-instance` (template 1.0.0) and profile `vm-instance` in plugin **1.5.0**.
  - New generic table keys `resolveSource` (with action `box1:development:resolve-source`) and `catalogEntity`.
  - `Kube.metadata()` for metadata-only reads.
  - New read-only Task `box1-bootc-status`.
- **Runbook:** `runbooks/service-decommission.md` now has a section for `virtual-machine` and `vm-instance`.

## Tests and deployment proof

All tests are local and listed in `evidence/02-local-tests.md` and `evidence/03-cross-check.md`.

**Not done, all blocked:**
- no CI run;
- no image built or deployed;
- no GitOps PR;
- no Developer Hub task;
- no VM.

**The two instances:** not created. Their namespaces would be `site-west-dev` and `site-east-dev`. Identities: `site_ds9` with client `site-west`, and `site_spacedock` with client `site-east`. Digests: none yet, because no `site-gateway-os` exists. Prepared inputs are in `site-inputs.md`.

**Promotion evidence:** file-level only. The first promotion and the day-2 `plan_instance_updates` touch only the promoted instance's directory.

**Measured resource use per VM:** not available. The estimate (200m CPU and 4372Mi requested per 2-vCPU/4Gi VM, from the observed `legacy-erp` and `vm-golden-check` launchers) is in `evidence/01-discovery.md`.

## Contract state

**Plugin action schemas:** one new action, `box1:development:resolve-source`. The existing actions keep their schemas apart from the profile enum, which gains `vm-instance`.

**GitOps contract:**
- `<instance>-site` is now required.
- The #140 keys and patterns are enforced.
- `keycloakTokenUrl` is accepted.
- Instance RBAC must exactly match the generated set.
- `box1-bootc-status` is added.

**Hub RBAC:** `get` on `imagestreamimages` in `box1-ci`, in box1-gitops#134.

## Operations and safety

**Secrets:** none created and none in Git. The cloud-init Secret is read as metadata only. The status key is a declared reference.

**Known risks:**
- Any `box1-ci` PipelineRun can use `ci-vm-deploy` and the status key. The forced command limits this to reading `bootc status`.
- The token URL host is not allowlisted.

**Day 2:** DataVolumes are never changed (D-006 on #139). An instance's OS changes in the guest through `bootc switch` to its pinned digest, which is #141's work.

**Rollback for each instance:**
- before the first promotion merges, revert the onboarding PR in `box1-workloads-dev` and follow the decommission runbook;
- after it, revert the instance's promotion PR (the VM goes back to Halted and zero digest; the DataVolume stays and needs the runbook), or decommission the instance with the updated runbook.

Template rollback: revert box1-templates#36 and pin plugin 1.4.0.

## What #141 needs from this profile

- Each instance's pinned `box1.org/os-image-digest` in `workloads/<instance>/virtualmachine.yaml`. The release promotes one instance per `box1-gitops-promote` call (`workload-profile: vm-instance`, `application-name: <source>`, `instance-name`).
- An in-guest, digest-pinned switch. The disk tracks `box1-ci/<source>:<channel>`, and the update timer is disabled in the image.
- The booted-digest proof through `box1-bootc-status`, which returns `booted-digest`.
- The adopted source revision and build run, recorded in each onboarding record (`source`).

## Next agent session

- **Next smallest slice:** after the merges and the plugin release, onboard `site-west` from Developer Hub (`site-inputs.md`), then `site-east`.
- **Files to read:** this directory, `plugins/box1-onboarding/README.md` § `vm-instance`, and box1-gitops `platform/pipelines/GOLDEN-PATH.md` § VM instance.
- **Blockers and owner decisions:**
  - approve `box1-ci/vm-instance-status-ssh` and the `box1-status` guest user (or choose another booted-digest mechanism, D-004);
  - deliver `site-gateway-os`;
  - create the Keycloak clients;
  - approve the cloud-init Secrets, the onboardings, the throwaway decommission instance and the regression VM.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#138
current_phase: "5 Review complete; stopped before 6 (dependencies unmerged, approvals pending)"
repositories:
  - name: box1-org/box1-templates
    branch: golden-path/138-vm-instance
    commit: 69f54c3c1ca364a5b05455d022ef1e2f9cb96f14
  - name: box1-org/box1-gitops
    branch: golden-path/138-vm-instance
    commit: 2030fcb1e3edd2522690c5321eca956a969a0719
  - name: box1-org/box1-docs
    branch: agent-run/138-vm-instance
    commit: (this PR head)
run_state_path: box1-docs/agent-runs/138-vm-instance/
requirements:
  proposed: 0
  implemented: 1
  locally_tested: 9
  ci_verified: 0
  deployed: 0
  live_verified: 0
  blocked: 3
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [security, operations]
open_decisions:
  - D-004 approval of box1-ci/vm-instance-status-ssh and the box1-status guest user
  - review finding 3 dedicated ServiceAccount for the status check
  - review finding 6 token URL host allowlist
rollback_state: nothing deployed; revert the PRs to roll back
next_action: owner merges box1-gitops 132→133→134, box1-templates 33→35→36, releases plugin 1.5.0
```
