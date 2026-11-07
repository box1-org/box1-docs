# Checkpoint: box1-docs#12 Service 02, frontier profile

**Updated:** 2026-11-05 17:30 EST
**Current phase:** 7. Deployed and partly live-verified. Stopped: the live acceptance order needs the user's explicit approval.

## Delivered

| Repository | Merged as | From |
|---|---|---|
| `box1-ops-contracts` | `e278940` | #5, head `85d72e3`, pinned by the service |
| `box1-gitops` | `2feea46` | #57; `box1-kafka` synced for the one topic |
| `box1-workloads-dev` | `bf71c01` | #57: floor, read policy `permit`, JVM OOM exit |
| `inventory-service` | `6b722a3` | #1 |
| `box1-workloads-dev` | `cd0c280` | #58, the pipeline's promotion |

Release `inventory-service-release-vgkx9`: build, gate (`policy=pass`), promote, smoke and `inventory-api-smoke` all passed. Live digest `sha256:d21ab42b4822428d0b6c1404261297bf03027701145f1486f78b6f447fd34531`, Argo `cd0c280` Synced/Healthy. See `evidence/08-release-live.txt`.

## Test results

| Run | Result | Evidence |
|---|---|---|
| Local suite with containers, at `5bd69c7` | 71 + 10 tests, 0 failures, SpotBugs 0, Checkstyle 0 | `evidence/04-scenarios-local.txt` |
| Local saga with the real order-service main | 23 of 23 checks, including 300-order load sample | `evidence/05-local-saga.txt` |
| CI `inventory-service-validate` at `5bd69c7` | pass, container-free tests only | `evidence/06-ci.txt` |
| Contracts at `85d72e3` | validate pass, 4 of 4 tests | `box1-ops-contracts#5` |

## Ledger

8 `live_verified`, 25 `deployed`, 1 `ci_verified`, 1 `blocked` (the live order). See `requirements.yaml`.

## Reviewer passes

All six are recorded in `review-findings/`. Release is conditional: the consumer path has not processed a post-floor event live.

## Open risks

- A reservation still unpublished past its `expiresAt`, after a broker outage longer than the 15-minute TTL, takes Order to `EXCEPTION`. That is Order's rule.
- A failed dead-letter send crash-loops the pod. Not tested, and avoided by merge order.
- Release tells Order nothing (no contract event). The runbook covers this.
- `/internal` routes have no usable client, so operator release and restock are impossible until D-010. Each live order's units stay held indefinitely, because no fulfillment adapter exists.
- Database credential: same template arrangement as the order run's D-005 (box1-docs#41). Specifics went to the user directly.
- A security review finding was reported to the user directly. Pointer: `review-findings/security.md` #2.
- Order's releases currently fail at promote. Not this run's to fix.

## Resume notes

```sh
export DOCKER_HOST=unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')
export TESTCONTAINERS_RYUK_DISABLED=true
podman machine ssh date; date -u   # check the VM clock first
caffeinate -ims ./mvnw clean verify -Pcontainers -DskipITs=false
python3 -I evidence/scripts/local-saga.py   # needs order-service built at order-e2e/ beside it
```

The workstation slept for 4 hours during this run despite `caffeinate`, so check the time before trusting a long run.

## Exact next action

1. **User approves** one live order through the Order Route: `POST https://order-service-dev.apps.ocp.box1.org/api/v1/orders` with a recorded `Idempotency-Key`, body `{"customerId":"cust_live_accept","sku":"SKU-42","quantity":2,"siteId":"site_nyc"}`. Its 2 units stay held, because no fulfillment adapter exists and D-010 keeps operator release closed.
2. Expect Order `FULFILLMENT_REQUESTED`, the hold `COMMITTED`, `site_nyc`/`SKU-42` available 98, one `inventory.reserved.v1`, and an empty dead-letter topic. Then mark `INV-LIVE-RESERVE` and the Release pass M2.
3. Follow-ups: tighten the served OpenAPI (Release L1); fix contract example `$ref`s (L2); a release event in contracts; pruning of outbox and dedupe rows; Order's consumer leaving its group during a database outage (local saga), for the Order owner.
