# D-011 Contract changes in box1-ops-contracts

**Status:** decided by the agent, Phase 1. Merge needs approval.

- Add `events/v1/equipment.threshold-exceeded.v1.schema.json` with the payload minima from `01_DOMAIN_CONTRACTS.md` (`assetId, siteId, metricName, value, threshold, severity`) plus optional `unit`, `alertId`, `measuredAt` and `sourceEventId` (the reading's `eventId`, AC5). Additive v1; the topic row already lists the event type.
- Add a fixture, `openapi/asset-service.yaml`, a `TELEMETRY.md` describing keying, alert semantics and the dead-letter topic, `TOPICS.md` row for `box1.telemetry.dlq.v1`, and the `OWNERSHIP.md` line for generated names `asset_service`.
- `equipment.reading.v1` is unchanged. The service applies stricter validation (metric allowlist, unit per metric, bounds) on top of it; a valid contract reading can still be rejected by service policy, which `TELEMETRY.md` states.
- The service's contract tests fetch the schemas from the pinned contracts commit, like inventory. No local copy.
