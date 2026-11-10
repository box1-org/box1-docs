# D-003 Buffer bound and overflow policy

**Decision.** Readings: at most 100 000 unpublished and at most 12 h old (older of `measuredAt` and receipt; checked
every 30 s); the oldest are dropped first and each drop is recorded in `outbox_drop` and counted
(`site_outbox_dropped_total{reason}`). Site events: at most 20 000 unpublished; never dropped; a new operator action
is refused (HTTP 503 `BUFFER_FULL`). Published rows kept 48 h for site-side counts.

**Why.** The simulator produces one reading per fixture asset every 5 s (about 17 300 a day); 100 000 rows is under
100 MB on the root disk's `/var`. asset-service rejects readings older than its 24 h retention, so 12 h leaves margin.
Operator actions are business data and must not be lost silently.
