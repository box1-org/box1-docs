# D-002 First-start offset policy for `box1.order.events.v1`

**Status:** shown to the user before deploy, and confirmed by them at about 17:05 EST ("Do what you think is best"). Live-verified: see `evidence/08-release-live.txt`.

**Risk:** the topic retains two `order.placed.v1` events, for live orders `ord_24a3...` and `ord_105f...`, not the one the brief expected. Both are `SUBMITTED`. Consuming either publishes an outcome, and Order then moves that live order to `FULFILLMENT_REQUESTED` or `REJECTED`.

**Policy:**

1. Group `inventory`, `auto.offset.reset=earliest`.
2. A required floor, `INVENTORY_ORDER_EVENTS_FLOOR`, an ISO-8601 instant with no default. Without it the application fails at startup, and `maxUnavailable: 0` leaves the old pod serving. An image cannot start consuming by accident.
3. An event of any type, on either consumed topic, with envelope `occurredAt` before the floor is acknowledged with no reservation, no outcome, no outbox row and no `processed_event` row. It is logged with its `orderId` and counted as `box1_events_consumed_total{outcome="skipped_before_floor"}`.
4. An event at or after the floor is processed normally.
5. A floor in the future also stops startup. A reviewer showed it would silently acknowledge real orders.
6. The floor is declared in `box1-workloads-dev` `workloads/inventory-service/deployment.yaml`, as a plain `env` entry, so it is reviewed and revertible. It is not in the generated ConfigMap, because a literal change there orphans a hashed ConfigMap and fails promote (box1-docs#42).
7. **Value:** chosen immediately before the merge, later than `2026-11-05T15:56:45.276583Z`, and after re-reading the topic to confirm which records it excludes. The PR is updated if any new order appeared.

**Why not `latest`:** it loses events placed between the floor moment and the first partition assignment. It also applies again whenever committed offsets vanish, for example after the group is empty for the broker's offset retention, and silently skips real orders. `earliest` plus dedupe makes that failure harmless, since every event already handled is a no-op.

**Why not pre-seeding group offsets:** that is a manual mutation of shared Kafka outside GitOps, and `auto.offset.reset=none` would make the service depend on it.

**Why `occurredAt` and not the record timestamp:** a replayed record gets a new record timestamp, but keeps `occurredAt`. So an operator replay cannot resurrect an excluded event. An order created before the floor and published after it is also excluded, correctly. A record with no valid `occurredAt` is poison.

**Consequences:**

- The two live orders stay `SUBMITTED`. They keep counting in Order's `box1_orders_stuck`. No inventory outcome will ever arrive for them unless the floor is deliberately lowered. Fixing them is an Order decision and out of scope here.
- The records age out at the 7-day retention. The floor stays harmless after that.
- Lowering the floor later and restarting does not rewind committed offsets. Reprocessing excluded events would need an approved offset reset.

**Proof planned:** a local test with a pre-floor record proves no reservation, no outcome and an advanced offset. After deploy: group offsets past the records, `box1.inventory.events.v1` still empty, both orders still `SUBMITTED`, and the counter at 2.

**Proof so far:** local tests and the local saga. Two orders placed before the floor stayed `SUBMITTED`, with no reservation, no inventory event, and the skip counter at 2. Re-checked live at 17:00 EST: still exactly the two records.
