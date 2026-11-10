# Handoff: box1-docs#139 GitOps validate/promote for vm-instance

## Work completed
- **Workstream:** golden path 02, `gitops-validate` and `gitops-promote` for `vm-instance`, plus the `ci/` rule for the `artifact` profile.
- **Repository and branch:** box1-org/box1-gitops, `golden-path/139-vm-instance-validate-promote`, head `147145f`.
- **PR:** https://github.com/box1-org/box1-gitops/pull/132 (open, not merged).
- **Changed paths:** `platform/pipelines/tasks/{gitops-validate.yaml,gitops-promote.yaml,test-gitops-validate.py,test-gitops-promote.py}`, `platform/pipelines/GOLDEN-PATH.md`.

## Tests and deployment proof
- **Before:** validate ran 14 tests with 2 failures (ServiceProfileRegression: legacy-erp, vm-golden-check); promote ran 23, OK.
- **After:** validate ran 68, OK; promote ran 31, OK (Python 3.11 and 3.9, kubectl 1.37.1 kustomize v5.8.1).
- Old and new validators are identical on 60 box1-workloads-dev revisions plus PR #126.
- Offline Task `__main__` run with fixtures: see `evidence/`.
- **Not verified:** no CI or Tekton run, no Argo sync, no deployment.

## Rules added and their exact messages
See box1-gitops `platform/pipelines/GOLDEN-PATH.md` § "VM instance workload profile" (rule table) and § "Code-only repository CI bundles". The code is the source of truth (`gitops-validate.yaml`).

## Contracts
- **Allowlist:** `VM_INSTANCE_SOURCES` tuple in `gitops-validate.yaml`, initially `('site-gateway-os',)` (D-001).
- **Source annotation:** `box1.org/source-image: <source>` on the VirtualMachine metadata (D-002).
- **Promote, for #138:** `workload-profile: vm-instance`, `application-name: <source repo>`, `instance-name: <instance>`, `disk-digest: <box1-ci/<source>-disk digest>` (D-003). See the example taskRef block in GOLDEN-PATH.md. `box1-vm-smoke` and `box1-bootc-apply` get the instance as `application-name`.
- **`ci/`, for #137:** D-004.

## Operations and safety
- **Secrets:** none created. The cloud-init Secret is referenced only, and assembled outside Git (#140).
- **Rollback:** revert PR #132, then sync `pipelines-ci`.

## Next agent session
See `checkpoint.md` § "Exact next action". Blockers: the owner merge and sync, and the D-006 decision.

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#139
current_phase: 6 (waiting on owner merge)
repositories:
  - name: box1-gitops
    branch: golden-path/139-vm-instance-validate-promote
    commit: 147145f1771775a7f4d8e82dcaadd0a4eff4ce3f
  - name: box1-docs
    branch: agent-run/139-gitops-vm-instance
    commit: (this PR)
run_state_path: box1-docs/agent-runs/139-gitops-vm-instance/
requirements:
  proposed: 2
  implemented: 1
  locally_tested: 6
  ci_verified: 0
  deployed: 0
  live_verified: 0
  blocked: 0
  superseded: 0
image_digest: n/a
gitops_commit: none (PR #132 unmerged)
review_passes_completed: [R-001 fresh subagent]
open_decisions: [D-006 day-2 DataVolume swap, D-005 CI follow-up issue]
rollback_state: nothing deployed; rollback = revert PR #132 + sync pipelines-ci
next_action: owner merges box1-gitops#132 and syncs pipelines-ci; then draft box1-workloads-dev vm-instance fixture PR
```
