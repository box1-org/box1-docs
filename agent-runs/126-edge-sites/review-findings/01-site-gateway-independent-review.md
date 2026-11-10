# Review pass 1: site-gateway (messaging, persistence, security, contracts, operations)

Fresh reviewer, given the diff (`1e0671b`), the contracts and the docs, not the implementation reasoning. Fixed in
`1d0eb0f` unless stated.

| # | Severity | Finding | Outcome |
|---|---|---|---|
| RF-1 | High (confirmed) | `send()` with no topic metadata waits `max.block.ms` per record and returns a failed future without throwing, so one 500-row batch could hold its row locks for ~83 min while disconnected | Fixed: metadata fetched once per batch (5 s bound), stop at the first failed future, producer kept on retriable errors |
| RF-2 | Medium | A record the database rejects (e.g. NUL in `sku`) rolled back the batch forever and stopped the pick-list consumer | Fixed: savepoint per record, SQLState 22/23 skipped and counted; containers test |
| RF-3 | Medium-low | Camel Paho connects before registering its callback; backlog delivered in the gap stays unacknowledged until a reconnect | Mitigated: one resync per client (D-007); the containers test passes with and without it |
| RF-4 | Low-medium | Concurrent double submit of a pick or hold release returned 409 instead of the first result | Fixed: advisory transaction lock on the requestId |
| RF-5 | Low | Age bound used receipt time, not `measuredAt` | Fixed: older of the two |
| RF-6 | Low | Metrics counted before commit | Fixed: counted after commit |
| RF-7 | Low | SIGTERM ignored while Flyway waits for the database at boot | Documented; bounded by the unit's stop timeout |
| RF-8 | Low | Pick-list thread could die on a RuntimeException; backoff not interruptible; no local expiry | Fixed the first two; local expiry deliberately not done (a committed reservation does not expire), documented |
| RF-9 | Info | Heartbeat reports the gateway's version for all modules | Documented (one bundle; `bundleDigest` is exact) |
| RF-10 | Info | First boot: readings before the first durable subscription are not kept | Documented; simulator now starts after the gateway |

No findings on: ack-after-commit, publish-after-ack, offsets after local commit, SQL on PostgreSQL, secrets in logs,
loopback binding, CSRF/CSP, contract conformance, readiness without Kafka.
