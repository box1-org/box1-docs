# D-005 Outbox, publish ordering, partition key and produced events

**Status:** decided by the run. The schemas need a box1-ops-contracts PR (D-013).

- `outbox` table and publisher copied from order-service: written in the same transaction as the terminal status change; claimed in bounded batches with `FOR UPDATE SKIP LOCKED` and a lease; at most the oldest unpublished row per `orderId` is claimed; sent outside the transaction with a dedicated `KafkaProducer` (`acks=all`, `enable.idempotence=true`); marked published only after the broker acknowledges. Failed sends back off 1 s doubling to 5 min and are never abandoned. Database clock only.
- Topic `box1.notification.events.v1`; record key and envelope `aggregateId` are `orderId` (the topic's contract partition key). Headers `eventType` and `eventId` only.
- Events: `notification.delivered.v1` on `DELIVERED`, `notification.failed.v1` on `FAILED`. One terminal event per intent, enforced by a unique index on `outbox (event_type, notification_id)`.
- Envelope: `correlationId` is the triggering event's `correlationId`; `causationId` is the triggering `eventId`; `traceparent` is the delivery span's context.
- A broker outage leaves terminal events in the outbox; they publish after recovery. Delivery and the API are unaffected. Kafka is not a readiness dependency; PostgreSQL is.
- `notification.requested.v1` stays out of scope (no producer).
- Delivery is at least once. Consumers of these events must dedupe by `eventId`.
