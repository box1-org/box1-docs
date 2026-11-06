# Inventory service: built, reviewed and deployed under the frontier profile

**Date:** 2026-11-05 (America/New_York)
**Status:** Deployed and partly live-verified. Closed as [box1-docs#12](https://github.com/box1-org/box1-docs/issues/12). The remaining live acceptance and follow-ups are in [box1-docs#47](https://github.com/box1-org/box1-docs/issues/47). Full run state, decisions and evidence are on branch [`agent-run/12-inventory-service`](https://github.com/box1-org/box1-docs/tree/agent-run/12-inventory-service/agent-runs/12-inventory-service).

## Outcome

`inventory-service` owns per-site stock, available-to-promise, reservations, expiry and rejection reasons. It consumes `order.placed.v1` and publishes exactly one outcome per order, through an outbox written in the same transaction. It is live in `inventory-service-dev`, delivered by the Golden Path pipeline with the security gate set to `gate`.

```text
image   image-registry.openshift-image-registry.svc:5000/box1-ci/inventory-service@sha256:d21ab42b4822428d0b6c1404261297bf03027701145f1486f78b6f447fd34531
source  box1-org/inventory-service 6b722a3
gitops  box1-org/box1-workloads-dev cd0c280 (Argo CD Synced/Healthy)
```

This was the second run under the `frontier` execution profile, after the [order-service pilot](https://github.com/box1-org/box1-docs/tree/agent-run/11-order-service/agent-runs/11-order-service). The agent owned discovery through deployment and stopped only for approvals.

## Starting baseline

- `inventory-service` had been onboarded through Developer Hub at 10:46 EST and ran only the scaffold (`5fed34f`). The prompt's proposed `box1-ops-inventory` did not exist, and the user chose the onboarded repository.
- `box1-ops-contracts` had inventory event schemas and an example migration. It had no inventory OpenAPI, no outbox, and no reservation state for consumed stock.
- `box1.order.events.v1` retained two `order.placed.v1` events for live test orders, both `SUBMITTED`. A consumer starting from the earliest offset would have moved them.
- The scaffold's release had `security-gates: disabled` and lacked the Guava override that order-service needed to pass the gate.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `box1-ops-contracts` | [#5](https://github.com/box1-org/box1-ops-contracts/pull/5) | `e278940` | Inventory OpenAPI, `INVENTORY-RESERVATIONS.md` (states and reason codes), `TOPICS.md` rows, aligned example migration |
| `box1-gitops` | [#57](https://github.com/box1-org/box1-gitops/pull/57) | `2feea46` | KafkaTopic `box1.inventory.dlq.v1`: 3 partitions, 14 days |
| `box1-workloads-dev` | [#57](https://github.com/box1-org/box1-workloads-dev/pull/57) | `bf71c01` | Deployment `env`: event floor, read policy `permit`, exit on heap OOM |
| `inventory-service` | [#1](https://github.com/box1-org/inventory-service/pull/1) | `6b722a3` | The service, tests, runbook, architecture, gate set to `gate`, API smoke task |
| `box1-workloads-dev` | [#58](https://github.com/box1-org/box1-workloads-dev/pull/58) | `cd0c280` | Promotion, opened and merged by the release pipeline |

**Decisions with consequences** (one record each in `decisions/` on the run branch):

- **First-start offsets (D-002).** The group `inventory` reads from the earliest offset, with a required floor, `INVENTORY_ORDER_EVENTS_FLOOR=2026-11-05T17:00:00Z`. Older events are acknowledged with no effect. The comparison uses the envelope's `occurredAt`, so a replay stays excluded. A missing, unparsable or future floor stops startup. The two retained orders stay `SUBMITTED` permanently. That is now an Order decision.
- **Reservation lifetime (D-003, D-009).** A hold is `ACTIVE` for 15 minutes, then `COMMITTED` and no longer expiring once Inventory reads `fulfillment.requested.v1`. Expiry also waits after startup, during and after consumer retries, after late events, and while the broker is unreachable. Order turns an expiry into `EXCEPTION`, so this protects healthy orders.
- **Shipment and release (D-004, D-005).** A shipment consumes the hold. A shipment after expiry or release opens a reconciliation item and reduces stock at most once. Release sends Order nothing, because the contracts have no such event.
- **Concurrency (D-006).** One conditional `UPDATE` per hold, at READ COMMITTED. A database `CHECK` keeps available from going negative.
- **Retries (D-007).** An unavailable database holds the channel without using attempts. Other failures are bounded at 20 attempts, then dead-lettered. A value the database can never store is dead-lettered at once.
- **Access (D-010, D-011).** Reads are anonymous, with no customer data. Operator restock and release need a Keycloak token with `inventory-admin` in the client's own claim. No such client exists, so these routes reject every call.
- **Database (D-012).** The generated name `inventory_service`, with the same template credential arrangement as order-service ([#41](https://github.com/box1-org/box1-docs/issues/41)).

## Validation and evidence

| Check | Result | Proof level |
|---|---|---|
| All 17 verification scenarios in #12: final-unit race, many concurrent orders, redelivery, equivalent order, crash and broker outage after commit, consumer restart, poison and schema mismatch, retry exhaustion and replay, clock-driven expiry, scheduler restart, expiry racing fulfillment and shipment, repeats, reason codes, unauthorized mutation, database down, customer data | 71 tests plus 10 packaged integration tests with real PostgreSQL 15 and Kafka 4.2.0: 0 failures. SpotBugs 0, Checkstyle 0. | Local |
| With the real `order-service` main, locally | 23 of 23 checks: reserve, each rejection reaching Order, final unit, Order down past the TTL, healthy order kept, runbook replay, database restart (ready again in 0.2 s), and 300 orders at about 5 per second (242 MiB RSS) | Local |
| Six reviewer passes | No high-severity findings. 4 medium and several low were repaired, and the full suite reran. Release pass conditional. | Review |
| Release `inventory-service-release-vgkx9` | Build, gate (`policy=pass`, SBOM accepted), promote, shared smoke and inventory API smoke all passed first time | Cluster |
| Running state | Pod digest, Argo revision and `/api/info` revision match. Flyway applied V1 and V2. | Live |
| Offset policy | Both retained events skipped (counter 2), group lag 0, both orders still `SUBMITTED`, inventory and dead-letter topics empty | Live |
| Read API and mutation boundary | Different values per site through the Route. 400 and 404 Problem responses. Anonymous mutations 401, read routes reject POST with 405. | Live |

**Not established live:** an order placed after the floor and its outcome reaching Order. That needs an approved test order, which is tracked in #47. The fault scenarios are local only, because no demo namespace exists for fault injection. Operator release and restock with a real token are not tested.

Most useful repairs found by verification and review:

- An unparsable floor left a running process with a dead consumer, because the bean was built lazily.
- After an outage, expiry could beat an unread fulfillment signal.
- A late shipment could take stock on every redelivery.
- A role could come from a top-level `groups` claim.

## Final operational state

- **Argo CD** manages `inventory-service` from `box1-workloads-dev` main, at `cd0c280`, automated with self-heal and no prune. `box1-kafka` (manual sync) now includes `box1.inventory.dlq.v1`.
- **Data:** seed fixture only. There are no reservations, and stock is at its seeded levels.
- **No temporary workarounds** are in place. Anonymous reads (D-011) and closed operator routes (D-010) are decisions, recorded with their consequences.

## Recovery and follow-ups

- **Rollback:** revert `box1-workloads-dev#58`. That restores the scaffold digest `4a1ae810…`, which has no datasource and ignores the tables. **Not exercised.** Migrations are forward-only, and the consumer group's offsets remain.
- **Operations:** the service's [runbook](https://github.com/box1-org/inventory-service/blob/main/docs/runbook.md) covers first deployment order, offsets, lag, outages, dead-letter replay and reconciliation.
- **Follow-ups in [#47](https://github.com/box1-org/box1-docs/issues/47):**
  - One approved live order end to end.
  - A Keycloak client if operator routes are wanted.
  - Served OpenAPI tightening.
  - Contract example `$ref` fixes.
  - A release event in contracts.
  - Outbox and dedupe pruning.
  - An order-service consumer that left its group during a local database outage, for the Order owner.
- **Reported to the user directly, not recorded here:** one security review finding, and the database credential details.
