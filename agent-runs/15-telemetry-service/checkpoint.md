# Checkpoint: box1-docs#15, frontier

**Current phase:** 7. Delivered (second release 828065e1, CORS fix). Live load run done and verified (`evidence/11`). Chaos half blocked by D-015 (pilot-log stop 2).
**Updated:** 2026-11-05 ~21:00 EST.

## Delivered
| Item | Result |
|---|---|
| box1-gitops#62 | merged 169dda0c; KafkaTopic box1.telemetry.dlq.v1 synced (only it, prune off), Ready |
| box1-gitops#63 | merged 39e2e8fe; KeycloakClient asset-service live (https callback accepted, http refused) |
| box1-workloads-dev#64 | merged 5ec7bf5d; PostgreSQL + PVC Bound; app env rolled |
| box1-ops-contracts#7 | merged d57a4efb (main merged into the branch first; pin 2fe191d on main) |
| asset-service#1 | merged 1706dd0b; release asset-service-release-rmcdq Succeeded: gate policy pass, promotion #72 (7a90162e), smoke pass |
| Running | digest sha256:4d8623986033b87bea25bed9461f0731e6616f47de00cc1bf21132dbbf0675d0, Argo Synced/Healthy at 7a90162e |

Evidence: `evidence/10-delivery.txt`. Ledger: 26 deployed, 5 live_verified, 1 proposed (TEL-LIVE-001).

## Open
- asset-service#2 (CORS fix) merged by the user, released as sha256:4d862398… (#74, aa0b4b04), verified on the Route.
- Client roles: created by the operator from the CR (an earlier note here said by hand; corrected).
- User: assign client role `chaos-operator` (client asset-service) to their account, sign in at https://asset-service-dev.apps.ocp.box1.org/console/, run one seeded load run. Then the agent records audit and readings evidence read-only.
- D-015 deferred: chaos stays off; the live chaos run (with alert and clear evidence) is blocked until a namespace is named.
- Release review pass: running/recorded in review-findings/release.md.
- Follow-ups filed: #60 (OpenAPI read scopes), #61 (VertxTracer noise), #62 (machine writer client, needs approval), #63 (session key, needs approval).

## Rollback
Revert box1-workloads-dev 7a90162e (promotion #72) to restore the scaffold digest sha256:0dc4185e…; tables, PVC, topic and client stay. Not exercised.

## Exact next action
After the user's console run: read `oc -n asset-service-dev logs deploy/asset-service` (read-only; run start, completion and alert lines), take the run ID, seed and sequence digest from the user's Recent runs view, and check the readings through the Route only if the user provides a bearer session. Record evidence for TEL-LIVE-001 (load part) and update the ledger. Do not run load on the cluster without a separate approval.
