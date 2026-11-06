# Checkpoint: box1-docs#15, frontier

**Current phase:** 6 entry. **STOPPED** for approvals and decisions (pilot-log stop 1). Phases 0 to 5 complete.
**Updated:** 2026-11-05 ~20:05 EST.

## Branches, commits and PRs (none merged)
| Repo | Branch | Commit | PR | What merging deploys |
|---|---|---|---|---|
| box1-gitops | telemetry-dlq-topic | 8bca2c0 | #62 | nothing until a selective `box1-kafka` sync (separate approval) |
| box1-gitops | asset-service-keycloak-client | b313754 | #63 | Keycloak client `asset-service` + 3 client roles in live realm `box1` (automated sync) |
| box1-workloads-dev | asset-service-runtime-config | bb0bcae | #64 | PostgreSQL + PVC + NetworkPolicy, Deployment env; needs the Secret first |
| box1-ops-contracts | asset-service-v1 | 2fe191d | #7 | nothing; service pins 2fe191d (repin if the merge rewrites it) |
| asset-service | telemetry-service | 490a7e2 | #1 | release: build, gate, promote, smoke into asset-service-dev |

## Evidence
- Local: `evidence/03` (tests), `04` (scenarios), `05` (browser), `06` (gate dependencies), `07` (review repairs). Screenshots in `evidence/screenshots/`.
- Suites: `./mvnw clean verify -Pcontainers` 62/62 at 742f9d7; CI-equivalent `-B clean verify -DskipITs=false` 45+5 at 11fa5a1.
- CI asset-service-validate-zr7tn at 11fa5a1: Succeeded (45 + 5 tests). Ledger: 10 ci_verified, 19 locally_tested, 1 implemented, 2 proposed.

## Open decisions (all reported together)
- D-012 approve merge of box1-gitops#62, then the selective sync of KafkaTopic `box1.telemetry.dlq.v1`.
- D-013 approve merge of box1-gitops#63; assign `chaos-operator` to the console user; decide who drives the live runs.
- D-014 choose the database credential option (recommended: out-of-band Secret; runbook command), and create it if agreed.
- D-015 deferred by the user ("another day"): chaos stays off; the cluster chaos run in Phase 7 is blocked by it.
- D-016 supply the brand-kit cube mark, or approve an interim option.
- Then approve, one at a time: workloads#64, contracts#7, asset-service#1; any Argo sync; Phase 7 live load run and chaos run.

## Exact next action
On approval of D-012, merge box1-gitops#62 and (on its own approval) sync only KafkaTopic box1.telemetry.dlq.v1 with prune off; confirm Ready. Then proceed down the table in order, checking the runbook preflight before asset-service#1.
