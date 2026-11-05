# Checkpoint: box1-docs#15, frontier

**Current phase:** 1 complete; entering 2 (contracts) and 3 (implementation).

## Completed
- Phase 0 discovery: `evidence/00-repositories.txt`, `01-cluster-baseline.txt`, `02-brand-search.txt`.
- Phase 1 decisions D-001 to D-011 decided; D-012 to D-016 open (user or approval).
- Requirement ledger `requirements.yaml`: 32 entries, all `proposed`.

## Branches
- box1-docs `agent-run/15-telemetry-service` (worktree `../run15-docs`).
- asset-service: clone `../run15-asset-service`, base `0dc14dc`, work branch to be `telemetry-service`.

## Open decisions (report together at the next stop)
- D-012 DLQ topic merge + box1-kafka selective sync (approval).
- D-013 Keycloak public client `asset-service` + roles (approval), and who drives the live console runs.
- D-014 database: recommended manifests in Git, Secret created out of band.
- D-015 chaos namespace name.
- D-016 brand mark asset.
- Private discovery findings: report directly to the user; pointer only here.

## Exact next action
Create branch `telemetry-service` in `run15-asset-service`; open the contracts branch `asset-service-v1` in a `run15-contracts` worktree for `equipment.threshold-exceeded.v1`.
