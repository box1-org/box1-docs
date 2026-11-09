# Local tests (2026-11-09, macOS, Node 20, Python 3.9, kubectl kustomize v5.8.1)

## box1-templates `golden-path/138-vm-instance` @ `69f54c3`

| Command | Result |
| --- | --- |
| `npm ci && npm run validate` | PASS. All existing renders are unchanged, plus `vm-instance` for `site-west`, `site-east` and a 35-character name, and the form's negative cases |
| `npm run test:onboarding` | 106 tests, 106 pass. Includes `scripts/test-onboarding-vm-instance.cjs`, the characterisation fixture (not regenerated) and the sync-equivalence test |
| `npm run test:onboarding-oci` | 26 tests, 26 pass |

## box1-gitops `golden-path/138-vm-instance` @ `2030fcb`

| Command | Result |
| --- | --- |
| `python3 platform/pipelines/tasks/test-gitops-validate.py` | 95 tests OK, 1 skipped (the live regression, run separately below) |
| `BOX1_WORKLOADS_DEV=<box1-workloads-dev b95b99b> python3 … ServiceProfileRegression` | OK: every live workload validates under its declared profile |
| `python3 platform/pipelines/tasks/test-gitops-promote.py` | OK |

## Not run

- Any live onboarding, Argo sync, VM boot or Hub task.
- The plugin package build (`package:onboarding-oci`).
