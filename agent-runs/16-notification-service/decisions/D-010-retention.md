# D-010 Retention

**Status:** decided by the run (configurable downward).

| Data | Kept | Mechanism |
|---|---|---|
| Terminal intents with their attempts, sources and receipts | 30 days after reaching `DELIVERED`/`FAILED` | daily purge, cascading delete |
| Non-terminal intents | until terminal (bounded by D-004 to ~1 min of retries) | — |
| `processed_event` | 30 days (longer than the 14-day source topic retention) | daily purge |
| Published outbox rows | 7 days | daily purge |
| `stub_fault_audit` | 90 days, append-only | purge allowed only after 90 days |

The fact-key uniqueness survives only as long as the intent. A replay older than 30 days is already excluded by the topic retention (≤ 14 days) and the event floor (D-006).
