# Checkpoint: box1-docs#138 `vm-instance` (frontier)

**Phase:** phases 0–5 are complete. The run stopped before phase 6 (GitOps delivery). The reasons are dependencies and approvals, not code. Updated 2026-11-09, America/New_York.

## Branches and PRs

| Repo | Branch | Base | Head | PR |
| --- | --- | --- | --- | --- |
| box1-templates | `golden-path/138-vm-instance` | `golden-path/137-artifact-profile` (#35) | `69f54c3` | [#36](https://github.com/box1-org/box1-templates/pull/36) |
| box1-gitops | `golden-path/138-vm-instance` | `golden-path/137-maven-bundle` (#133) | `2030fcb` | [#134](https://github.com/box1-org/box1-gitops/pull/134) |
| box1-docs | `agent-run/138-vm-instance` | `main` | see PR | this run's PR |

## Changed files

**box1-templates:**
- `templates/vm-instance/**`
- `catalog-info.yaml`
- `plugins/box1-onboarding/{workflow.cjs,index.cjs,README.md,package.json,oci-package.json}`
- `scripts/{validate.mjs,test-onboarding-vm-instance.cjs,test-onboarding-characterisation.cjs,test-onboarding-profiles.cjs,test-onboarding-vm.cjs}`
- `package.json`

**box1-gitops:**
- `platform/pipelines/tasks/{gitops-validate.yaml,test-gitops-validate.py,bootc-status.yaml,kustomization.yaml}`
- `platform/pipelines/GOLDEN-PATH.md`
- `platform/developer-hub/onboarding/access.yaml`

**box1-docs:**
- `runbooks/service-decommission.md`
- `agent-runs/138-vm-instance/**`

## Test results

Details are in `evidence/02-local-tests.md`.
- `test:onboarding`: 106/106 pass.
- `validate`: PASS.
- `test:onboarding-oci`: 26/26 pass.
- `test-gitops-validate`: 95 OK.
- Live regression against workloads: OK.
- `test-gitops-promote`: OK.
- Cross-check: `evidence/03-cross-check.md`.

## Blocked and open

**Dependencies not delivered:**
- #136, #137, #139 and #140 are open PRs.
- `site-gateway-os` does not exist.

**Approvals needed:**
- Secret `box1-ci/vm-instance-status-ssh`.
- `box1-status` user in the source image.
- Per-site Keycloak clients (#131).
- Each `<instance>-cloud-init` Secret.
- Developer Hub onboarding.
- The throwaway decommission instance.
- The regression VM.

**Open review findings:** 3 (dedicated ServiceAccount), 6 (token URL host allowlist), 8 (resume parameter hash) and 9 (ResourceQuota). See `review-findings/01-security-operations.md`.

## Exact next action

The owner reviews and merges, in this order with about 10 s between merges (box1-docs#64):
1. box1-gitops#132 → #133 → #134;
2. box1-templates#33 → #35 → #36;
3. Release plugin 1.5.0 by tagging `onboarding-plugin-v1.5.0` on the merge commit. Do not release 1.3.0 and 1.4.0 separately unless wanted.

Then:
- Merge the box1-gitops plugin PR that CI opens, and sync the Hub.
- Deliver `site-gateway-os` (#126) with cloud-init and the `box1-status` user.
- Approve the status key, then follow `site-inputs.md`.
