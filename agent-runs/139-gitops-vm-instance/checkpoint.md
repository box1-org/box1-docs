# Checkpoint: box1-docs#139 (frontier), 2026-11-08 (America/New_York)

## Current phase
Phases 0–5 are complete. Phase 6 (delivery) is waiting on the owner to merge box1-org/box1-gitops#132 and sync `pipelines-ci`. Phase 7 (live acceptance) has not started.

## Completed
- **Discovery**
  - box1-gitops main is `4bcc907`; box1-workloads-dev main is `b95b99b` (11 workloads; no `ci/`).
  - The only open box1-workloads-dev PR is #126.
  - Promote callers (grep): box1-templates `quarkus-rest-service` and `rhel-image-vm` skeletons, `vm-golden-check`, and legacy-erp `release.yaml` and `appliance-pipeline.yaml`. None passes `instance-name`. The plugin `workflow.cjs` only mirrors the first VM promotion (L570) and checks the `virtual-machine` label (L120).
  - KubeVirt CRD (OpenShift Virtualization 5.0.0) has `cloudInitNoCloud.secretRef`. Stop condition not hit.
- **Baseline tests** (`evidence/baseline-*.txt`):
  - validate ran 14 tests (13 VirtualMachineProfile + 1 regression; the prompt said 14 VM cases, the actual count is 13). With `BOX1_WORKLOADS_DEV` set, `ServiceProfileRegression` **FAILED** for legacy-erp and vm-golden-check (`'virtual-machine' != 'service'`). Without it, OK with 1 skipped.
  - promote ran 23 tests, OK.
- **Design decisions:** D-001 to D-007 in `decisions/`.
- **Implementation:** tests first in `57c171e` (`evidence/tests-first-*.txt` shows the new cases failing), implementation in `fade118`, review fixes in `147145f`.
- **Verification:**
  - validate ran 68 tests and promote 31, all OK on Python 3.11 and 3.9;
  - regression on PR #126 head OK;
  - old vs new validator identical on 60 main revisions plus PR #126;
  - offline `__main__` end-to-end run with fixtures (`evidence/validator-main-offline.txt`).
- **Review:** R-001 found 4 security gaps; all fixed with tests.

## Changed files (box1-gitops)
`platform/pipelines/tasks/gitops-validate.yaml`, `gitops-promote.yaml`, `test-gitops-validate.py`, `test-gitops-promote.py`, `platform/pipelines/GOLDEN-PATH.md`.

## Open risks
- D-006: day-2 DataVolume swap deviates from the owner decision; needs sign-off.
- Merging plus syncing `pipelines-ci` changes the required check on all box1-workloads-dev PRs at once. Re-check open box1-workloads-dev PRs right before the sync.
- #141 requirement: the bootc-disk update source is the shared `:<channel>` tag (GOLDEN-PATH.md "Channels").

## Exact next action (owner)
1. Review and merge box1-gitops#132. Then sync the Argo Application `pipelines-ci` and confirm it shows the merge revision and that both Tasks are updated (`oc get task -n box1-ci box1-gitops-validate -o yaml` contains `VM_INSTANCE_SOURCES`).
2. Live acceptance, allowed only after step 1:
   - Open a **draft** box1-workloads-dev PR that adds `workloads/site-west/` (a vm-instance fixture of `site-gateway-os`; generate it with `evidence/scripts/make-fixture-tree.py`, or by hand from `instance_bundle()` in `test-gitops-validate.py`).
   - Confirm `box1-gitops-validate` passes. Push one negative commit (for example inline `userData`) and confirm it fails with the readable message.
   - Close the PR unmerged and record the PipelineRun names here.
   - Do not add `applications/site-west.yaml`, so nothing deploys.
3. Observe the first real service release and the first VM release after the sync passing `box1-gitops-validate`.
4. Decide D-006 on #139. File the D-005 follow-up issue. Tick the #139 checklist items only with the evidence above.
