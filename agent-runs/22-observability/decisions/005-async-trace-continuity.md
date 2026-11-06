# 005 Trace continuity across the outbox, Kafka and the ERP

**Observed:** the consumers in order, inventory and notification make the envelope `traceparent` the span parent. That gives one connected trace per order, from POST through the outbox and Kafka.

**Decision:**
- Keep parent-based continuation for now, as it meets "one trace from orderId". Add span links only if delayed processing makes parent spans misleading. Record that as a finding in Phase 4 rather than changing four services up front.
- The fulfillment-adapter Kafka consumer creates no span. Adding one belongs in a PR to that service's repo, which is a later slice.
- Across the ERP, correlate by `fulfillmentRequestId` only (prompt rule).
