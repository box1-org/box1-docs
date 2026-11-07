# D-003 Deduplication: one business fact, one intent, one effective delivery

**Status:** decided by the run.

Two layers, both in the same database transaction as the intent insert:

1. **Event layer** — `processed_event(event_id)` with `INSERT … ON CONFLICT DO NOTHING`, as in order-service and inventory-service. A redelivered event is a no-op.
2. **Fact layer** — `notification.dedupe_key` is `UNIQUE`. The key is built from the business fact only (D-002 table): `orderId`, notice type and, where a fact can recur for an order, the triggering qualifier. It never contains `eventId`, offsets or arrival time.

Cross-event mapping: `SHIPPED` state change and `shipment.confirmed.v1` both map to `ORDER_SHIPPED:{orderId}`; non-retryable `shipment.failed.v1` and `EXCEPTION/SHIPMENT_FAILED` both map to `SHIPMENT_FAILED:{orderId}`. The second event inserts `INSERT … ON CONFLICT (dedupe_key) DO NOTHING`, then records itself in `notification_source(notification_id, event_id, event_type)` so the operator API shows both sources.

`SHIPMENT_DELAYED` includes `fulfillmentRequestId` and `reasonCode`, so a repeat of the same retryable failure is one notice, while a different reason is a new notice.

**Effective delivery** is one receipt per intent: `delivery_receipt.notification_id` is `UNIQUE`, and the provider is called with `notificationId` as its idempotency key (D-004), so a retried call after a crash returns the existing receipt.
