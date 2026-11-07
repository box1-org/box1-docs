# Checkpoint: box1-docs#13 Service 03, frontier profile

**Updated:** 2026-11-05 21:15 EST
**Current phase:** 7, stopped
**Stop reason:**
- A live Kafka fulfillment needs D-015 (a live order).
- SFTP and the two VM criteria need #25 and D-007.

## Delivered

| Repository | Merged as | From |
|---|---|---|
| box1-ops-contracts | d21d91f | #8 |
| box1-gitops | 0f5ff2d | #64, plus a `box1-kafka` sync of KafkaTopic `box1.fulfillment.dlq.v1` only |
| box1-workloads-dev | ff2595b | #65 (database; Secret created by the user) |
| fulfillment-adapter | 0a44cc6 | #1 |
| box1-workloads-dev | 3668f3b | #73 (promotion, auto-merged by the release pipeline) |

**Deployed:** `sha256:9247f98fee515d8fad98d9c4665e84c9464dc2be94a02215958b9cc54ec6a931`. Argo `fulfillment-adapter` is Synced/Healthy at `3668f3b`.

## Test results
- Local: 123 tests + 5 ITs; 50/50 scenarios; TUI 6/6 (evidence/05-after-review.txt).
- CI: evidence/06-ci.txt.
- Release and live checks: evidence/07-release-live.txt.

## Ledger
5 live_verified, 18 deployed, 2 ci_verified, 1 locally_tested, 1 implemented, 2 blocked (AC03, AC04: the ERP VM).

## Open risks
- No live fulfillment has run yet.
- Rollback not exercised.

## Exact next action
1. Done: D-002 complete. The first live REST fulfillment `ful_demo1` was accepted (202) and is QUEUED (evidence/07-release-live.txt).
3. When #25 exists and D-007 is approved: provision the SFTP Secret, enable SFTP in the workloads, and run the VM round trip and TUI shipment.

Achievement log: box1-docs#58 (open). Operator helper: fulfillment-adapter#2 (open, CI passed).
