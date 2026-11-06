# Checkpoint: box1-docs#15, frontier

**Current phase:** 4 complete; Phase 5 (reviewer passes) starting.
**Updated:** 2026-11-05 ~19:20 EST.

## Branches, commits and PRs (none merged)
| Repo | Branch | Commit | PR |
|---|---|---|---|
| asset-service | telemetry-service | 3c40e8c | https://github.com/box1-org/asset-service/pull/1 |
| box1-ops-contracts | asset-service-v1 | 8764f7d | https://github.com/box1-org/box1-ops-contracts/pull/7 |
| box1-workloads-dev | asset-service-runtime-config | df641af | https://github.com/box1-org/box1-workloads-dev/pull/64 |
| box1-gitops | telemetry-dlq-topic | 8bca2c0 | https://github.com/box1-org/box1-gitops/pull/62 |
| box1-gitops | asset-service-keycloak-client | 95206e7 | https://github.com/box1-org/box1-gitops/pull/63 |

## Tests and evidence
- `./mvnw clean verify -Pcontainers` at 5fdfe89: 52 tests, 0 failures, static analysis clean; RetentionTest (2) added at 3c40e8c and passing.
- Phase 4 scenarios all PASS locally: `evidence/04-scenarios-local.txt`. Browser checks (headless Firefox, axe, keyboard): `evidence/05-browser-local.txt`, `evidence/screenshots/`.
- Ledger: 29 locally_tested, 1 implemented (docs), 2 proposed (delivery, live).

## Local environment
Containers run15-pg :15432, run15-kafka :19092, run15-keycloak :18180; app on :18080 (scratch run-local.sh, PID file app.pid). Scratch scripts mirrored in evidence/scripts.

## Open decisions (report together at the Phase 6 stop)
- D-012 merge box1-gitops#62 and selectively sync KafkaTopic box1.telemetry.dlq.v1.
- D-013 merge box1-gitops#63; assign chaos-operator; who drives the live console runs.
- D-014 database Secret: recommended out of band (runbook command), no password in Git.
- D-015 chaos namespace name.
- D-016 brand mark asset.
- Then merges in order: workloads#64, contracts#7 (repin if rewritten), asset-service#1.
- Private discovery findings: reported directly to the user.

## Exact next action
Run reviewer passes (architecture, persistence, messaging, security incl. console and Route, operations) on asset-service 3c40e8c vs 0dc14dc plus the four other PR diffs; record findings in review-findings/; fix; rerun the full suite. The Release pass waits for deployment.
