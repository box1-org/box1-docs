# D-007 Kafka evidence window

**Status:** the window was decided by the user; the values below are proposed. The contracts PR needs approval.

- **Topics:** `box1.{order,inventory,fulfillment,notification}.events.v1`, plus `box1.telemetry.events.v1`, from which only `equipment.threshold-exceeded.v1` is kept. Readings are dropped because of their volume. DLQs are not read; that would be a contract change.
- **Consumer group:** `agentic-operations` on all five topics. The `TOPICS.md` row's reserved `ai-operations` is renamed to `agentic-operations`, and the group is added to the other four rows. This is a box1-ops-contracts PR.
- **Offsets:** no committed offsets (`enable.auto.commit=false`, with no commit strategy). On partition assignment, the consumer seeks to `now − AIOPS_WINDOW_AGE` (default `6h`) with offsetsForTimes. The window rebuilds after a restart, and the group never holds offsets other services depend on.
- **Bounds and indexes:**
  - at most `AIOPS_WINDOW_MAX_EVENTS=20000` events in total and 200 per key;
  - indexed by `orderId`/`assetId` (`aggregateId`) and `correlationId`;
  - deduplicated on `eventId`, or on `alertId` for threshold alerts.
- **Stored fields:** envelope fields and a bounded, schema-validated payload (unknown fields dropped). Notes and free-text fields are capped and kept as untrusted data.
- **Poison records** (unparseable, missing envelope fields or unknown `eventType`): skipped, counted in `aiops_kafka_records_skipped_total{topic,reason}`, and logged with topic, partition and offset only. Nothing is written to any DLQ: the service is read-only and does not own the DLQs.
- **Health and metrics:** Kafka is not part of readiness. The window exposes `aiops_window_events`, `aiops_window_oldest_age_seconds` and per-partition consumer lag. An empty window reads as "no recent events", never as an error.
- **Retry path:** the contract requires a bounded retry path. That is met by skipping, because the window is a best-effort cache and the authoritative state stays in the owning services' APIs.
