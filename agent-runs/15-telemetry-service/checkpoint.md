# Checkpoint: box1-docs#15, frontier

**Current phase:** 7. Delivered and verified live; waiting for the user-driven console load run (pilot-log stop 2).
**Updated:** 2026-11-05 ~21:00 EST.

## Delivered
| Item | Result |
|---|---|
| box1-gitops#62 | merged 169dda0c; KafkaTopic box1.telemetry.dlq.v1 synced (only it, prune off), Ready |
| box1-gitops#63 | merged 39e2e8fe; KeycloakClient asset-service live (https callback accepted, http refused) |
| box1-workloads-dev#64 | merged 5ec7bf5d; PostgreSQL + PVC Bound; app env rolled |
| box1-ops-contracts#7 | merged d57a4efb (main merged into the branch first; pin 2fe191d on main) |
| asset-service#1 | merged 1706dd0b; release asset-service-release-rmcdq Succeeded: gate policy pass, promotion #72 (7a90162e), smoke pass |
| Running | digest sha256:6d8e8c172b2885f35a551eb34c53429e1ac85a1771263ba841795c683fbde944, Argo Synced/Healthy at 7a90162e |

Evidence: `evidence/10-delivery.txt`. Ledger: 26 deployed, 5 live_verified, 1 proposed (TEL-LIVE-001).

## Open
- User: assign client role `chaos-operator` (client asset-service) to their account, sign in at https://asset-service-dev.apps.ocp.box1.org/console/, run one seeded load run. Then the agent records audit and readings evidence read-only.
- D-015 deferred: chaos stays off; the live chaos run (with alert and clear evidence) is blocked until a namespace is named.
- Release review pass: running/recorded in review-findings/release.md.
- Follow-ups: OpenTelemetry VertxTracer warning noise per request; machine client for telemetry-writer (ARCH-10); Secret-backed session key (SEC-5); catch-up memory measurement (OPS-11).

## Rollback
Revert box1-workloads-dev 7a90162e (promotion #72) to restore the scaffold digest sha256:0dc4185e…; tables, PVC, topic and client stay. Not exercised.

## Exact next action
After the user's console run: read `oc -n asset-service-dev logs deploy/asset-service` (read-only; run start, completion and alert lines), take the run ID, seed and sequence digest from the user's Recent runs view, and check the readings through the Route only if the user provides a bearer session. Record evidence for TEL-LIVE-001 (load part) and update the ledger. Do not run load on the cluster without a separate approval.
