# D-001 Site event family, site topic and status API

**Decision (2026-11-10).** Three closed payloads, `site.pick-confirmed.v1`, `site.stock-adjusted.v1` (cycle count)
and `site.stock-held.v1`, on `box1.site.events.v1` keyed by `siteId` (`aggregateId` = `siteId`), DLQ
`box1.site.dlq.v1`, consumer groups `inventory-site` and `site-gateway-<siteId>`. `eventId` is a random UUID created
with the site action; `pickId`/`countId`/`holdId` are the site-local identities. Header `box1-site-id`
(informational until #71). Status API in asset-service: `PUT /api/v1/sites/{siteId}/status`, `GET /api/v1/sites`,
`GET /api/v1/sites/{siteId}`; states ONLINE / DEGRADED / OFFLINE (defaults 90 s, depth 200, oldest 5 min, greenboot RED).

**Why.** The envelope pattern allows exactly two dot segments, so `site.pick-confirmed.v1`, not
`site.pick.confirmed.v1`. Keying by `siteId` orders a site's actions. Status lives in asset-service (#126 decision).

**Where.** box1-ops-contracts#14 (`SITE.md`, `TOPICS.md`, `TELEMETRY.md`, `events/v1/site.*`, `openapi/asset-service.yaml`).
