# D-010 Kafka first-start offset policy

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Decision:** group `fulfillment`, `auto.offset.reset=earliest`, no floor. Other event types on `box1.order.events.v1` are acknowledged without effect.

**Why:** a skipped `fulfillment.requested.v1` leaves its order in `FULFILLMENT_REQUESTED` forever; dedupe by `fulfillmentRequestId` makes replay harmless. Discovery found no sign that any `fulfillment.requested.v1` was ever produced (both live orders are `SUBMITTED`), so earliest dispatches nothing old. Re-check order metrics before the first deploy.
