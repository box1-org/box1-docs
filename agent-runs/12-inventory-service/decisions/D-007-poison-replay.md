# D-007 Retries, poison, dead letters and replay

**Status:** decided by the agent in Phase 1, 2026-11-05. The dead-letter topic is a shared-infrastructure PR that needs approval.

- **Database cannot serve** (no SQLState, or classes 08, 53, 57P): the channel holds position, retrying at most every 30 s, using no attempts. Revised in Phase 5: reviewers showed a dead-lettered valid `fulfillment.requested.v1` damages a healthy order even with a correct replay. It is visible through `box1_inventory_consumer_held_for_database_total` and readiness. This is an unbounded wait by decision, and differs from the deployed Order service.
- **Other transient errors:** 20 attempts, 500 ms doubling to a 30 s cap, about 7 minutes, then the dead-letter topic.
- **A value that can never be stored** (SQLState 22, or 23 except 23505): straight to the dead-letter topic.
- **Poison, no retries:** invalid JSON, invalid envelope or payload, `schemaVersion` other than 1, an `eventType` not expected on that topic, `aggregateId` not matching `orderId`, and an `order.placed.v1` for a known `orderId` whose `sku`, `quantity` or `siteId` differ from the recorded decision.
- **Dead-letter topic:** new `box1.inventory.dlq.v1`, 3 partitions, 14 d, via the connector's dead-letter strategy. It carries the original value unchanged, with fixed-text cause headers. **It must exist before the service ships**: a failed dead-letter send restarts the pod, and the broker's auto-create would otherwise make a one-partition topic with default retention.
- **Inspection:** `box1_inventory_dlq_depth`, from an admin client reading end minus beginning offsets, plus the `dead_lettered` counter.
- **Replay:** a runbook procedure re-producing the record to its source topic. Recorded who and why. No HTTP replay route.
- **No re-publish under a new outcome:** `order_outcome(order_id PK)` holds the first decision. A replay, or the same order under a new `eventId`, returns the stored decision and writes no outbox row, even if stock has changed since. A partial unique index on `outbox (aggregate_id, event_type)` guards this at the database.
- **Tolerant reader:** unknown fields in a v1 payload are ignored, per additive-change governance.
- **Publisher:** the same at-least-once design as Order. `FOR UPDATE SKIP LOCKED`, a lease, oldest-per-order only, marked published only after the broker confirms, retrying with a capped backoff. Claim and retry times use the database clock.
