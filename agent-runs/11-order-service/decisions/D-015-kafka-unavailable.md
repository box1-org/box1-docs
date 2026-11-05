# D-015 Behavior when Kafka is unavailable

**Status:** decided by the agent in Phase 1, 2026-11-05.

- Order creation keeps working. The order and outbox row commit, and the API returns 201.
- Readiness stays UP. Kafka is not a readiness dependency, so a broker outage does not take the API out of the Route. PostgreSQL is a readiness dependency.
- `box1_outbox_pending` and the oldest-pending age rise, and are the outage signal.
- Publisher: claims a bounded batch with `FOR UPDATE SKIP LOCKED` and a lease, commits, sends outside the transaction with `acks=all` and idempotence, marks published only after the broker confirms. Only the oldest unpublished event per order is claimed, preserving per-order order.
- Delivery is at least once. A crash after broker ack and before marking re-sends the same `eventId`, and consumers dedupe on it.
