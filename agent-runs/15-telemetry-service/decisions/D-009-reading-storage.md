# D-009 Reading storage, retention and partitioning

**Status:** decided by the agent, Phase 1.

- **Owner:** the service's own PostgreSQL database (generated name `asset_service`). No other service reads it.
- **Path:** HTTP or load -> validate -> Kafka `box1.telemetry.events.v1` (key `assetId`) -> this service's consumer (group `asset-service`) -> `reading` table and threshold engine in one transaction. The read model is a projection of the topic, which is what makes Kafka lag a meaningful readout.
- **Duplicates:** primary key `(asset_id, metric_name, measured_at)`; `INSERT ... ON CONFLICT DO NOTHING`. A duplicate reading (same asset, metric and instant) is stored once and not re-evaluated. Its `eventId` is kept as `source_event_id` for evidence.
- **Retention:** readings older than `asset.retention.readings` (default PT24H) are deleted in batches of 5000 every minute; a hard row cap (`asset.retention.max-rows`, default 2,000,000) deletes oldest rows beyond it. Cleared alerts older than 30 days and audit older than 90 days are deleted by the same job.
- **Partitioning:** Kafka is partitioned by `assetId` (6 partitions, per-asset order). The table is not declaratively partitioned: at 100 readings/s and 24 h it holds at most ~8.6 M rows, but the row cap bounds it at 2 M. If retention or rate grows past that, daily range partitions with `DROP PARTITION` replace batched deletes; documented in the runbook as the switch point.
- **Query:** `GET /api/v1/assets/{assetId}/readings?from=&to=&metric=&limit=&cursor=` orders by `(measured_at, metric_name)` ascending; the opaque cursor encodes the last `(measured_at, metric_name)`; keyset pagination gives stable pages while new readings arrive. `limit` 1 to 500, default 100. Window at most 24 h.
