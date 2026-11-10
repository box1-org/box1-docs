# D-002 Readings stay on the telemetry topic, keyed by assetId

**Decision.** Site readings are ordinary `equipment.reading.v1` on `box1.telemetry.events.v1`, key `assetId`,
`causationId` `ingest:site`, `eventId` = Java `UUID.nameUUIDFromBytes("box1/equipment.reading.v1/<assetId>/<metricName>/<measuredAt>")`
(now stated in `TELEMETRY.md`, with a site reading as test vector checked by both the contracts tests and site-gateway).

**Why.** #127 says "every event is keyed by siteId", but the readings contract keys by `assetId`; changing it would
be a breaking contract change (02 prompt stop condition). The `siteId` key applies to site events (D-001).
asset-service deduplicates on the natural key, which this `eventId` derivation makes equivalent.
