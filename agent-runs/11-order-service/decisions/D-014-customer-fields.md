# D-014 Customer fields in logs and events

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **Events:** `customerId` only in `order.placed.v1`, because the contract requires it. It is an opaque `cust_` ID. Other events omit it.
- **Logs:** `orderId`, `eventId`, `eventType`, `correlationId`, trace IDs and state. Never `customerId`, `Idempotency-Key`, `X-Consumer-Id` or payload bodies.
- **Dead-letter records:** carry the original value unchanged, so the topic has the same sensitivity as its source.
- **API:** `customerId` is returned on orders, as the contract requires. With D-003 this makes it readable on the LAN, tracked in box1-docs#40.
