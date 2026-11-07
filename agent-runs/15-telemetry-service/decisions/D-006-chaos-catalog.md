# D-006 Chaos catalog and bounds

**Status:** decided by the agent, Phase 1. Telemetry-only: every entry acts on this service's generated readings or its own producer. Faults in Kafka, Order, Inventory or ERP belong to #19.

A chaos run is a load run plus injections. The next injection starts after a seeded interval of 5 to 30 s (uniform). At most one injection is active per run. Each lasts at most 30 s and is recorded in the audit with its parameters.

| Entry | Effect | Bounds |
|---|---|---|
| `BURST` | Multiplies the run's rate | 2x to 5x, 5 to 15 s, capped by the shared ingestion rate |
| `SPIKE` | One reading of one asset at 1.2 to 1.5x its critical threshold | single reading |
| `SUSTAINED_BREACH` | One asset/metric above warning threshold | 10 to 30 s |
| `FLAP` | One asset/metric alternates just above trigger and just above clear level (inside the hysteresis band) | 10 to 30 s |
| `STALE_ASSET` | One asset stops sending | 10 to 30 s |
| `CLOCK_SKEW` | `measuredAt` shifted by +2 to +10 min (beyond the 5 min future limit: rejected) or -1 to -30 min (accepted) | 5 to 15 s |
| `OUT_OF_ORDER` | Readings in a window of 3 to 8 are emitted in shuffled order | 5 to 15 s |
| `DUPLICATE` | Re-submits the previous reading verbatim | 1 to 10 readings |
| `INVALID_UNIT` | Wrong unit for the metric | 1 to 5 readings, all rejected |
| `INVALID_PAYLOAD` | Missing field, non-finite or out-of-bounds value, unknown metric | 1 to 5 readings, all rejected |
| `OVERSIZE_PAYLOAD` | Body padded past 4 KiB | 1 to 3 submissions, all rejected 413-equivalent |
| `PRODUCER_PAUSE` | Pauses this service's Kafka producer; queue fills to its bound, then backpressure rejections | 5 to 30 s, auto-resume |

Not in the catalog by design: killing pods, touching the database, broker or network, or any other service.
