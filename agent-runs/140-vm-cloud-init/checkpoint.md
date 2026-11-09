# Checkpoint: box1-docs#140 VM cloud-init (frontier)

## Current phase

Phase 5 (review) is complete. The run stopped at the authorization boundary: phases 6 and 7 need merges and cluster changes that the unattended run could not make. Updated 2026-11-08 (America/New_York).

## Completed

- **Discovery** (`evidence/01-discovery.md`):
  - KubeVirt v1.9.0 / OpenShift Virtualization 5.0.0 supports `cloudInitNoCloud.secretRef`.
  - The NoCloud instance-id is the firmware UUID, which is random per VirtualMachine object (from source; the stored UUID on `vm-golden-check` is not name-derived).
  - The base image has no cloud-init.
  - cloud-init 24.4 re-reads a disk seed on each boot.
- **Decisions** D-001 to D-006 (`decisions/`).
- **box1-templates PR #34** (`golden-path/140-cloud-init`, `390cd79`): the `cloudInit` parameter, the `rootfs-cloud-init/` tree, and the Containerfile and validate.mjs changes.
- **box1-docs PR #147** (`golden-path/140-cloud-init-runbook`): the assembly script with 16 tests, the runbook, this run state, and the test plan.
- **Security reviewer pass**: findings and repairs in `review-findings/security.md`.

## Test results

- `npm run validate`, `VM_BASELINE_REF=origin/main npm run validate`: pass.
- `npm run test:onboarding`: 57/57.
- Script tests: 16/16. See `evidence/02-local-tests.md`.

## Ledger

| Status | Requirements |
| --- | --- |
| `locally_tested` | 2 (no credential in Git; existing VMs and off-render unchanged) |
| `implemented` | 5 |
| `proposed` | 1 (the failure scenarios) |

None is live-verified.

## Open risks

- Not yet observed:
  - the RHEL 10 `cloud-init` version and unit names;
  - `bootc container lint` with cloud-init;
  - whether the installed RHDH skips empty-rendered paths;
  - the guest instance-id behavior;
  - the status KubeVirt reports when the Secret is missing.
- The module lists are not a security boundary: Secret write access is root in the guest. An admission check is a follow-up for #138/#139.
- The token URL host and realm are not pinned in the script (security finding 9, partly fixed).

## Exact next action

1. The owner reviews and merges box1-templates#34, then box1-docs#147, waiting about 10 s between merges (#64).
2. With approval, run `test-plan/README.md` steps 1–7.
3. Record the results in `evidence/10-live-boot.md`, update `requirements.yaml`, and tick #140's acceptance items with that evidence. Hand the real-instance re-run to #138.
