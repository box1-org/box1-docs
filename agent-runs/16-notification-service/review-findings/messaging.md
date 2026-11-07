# Messaging pass

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`).

No-finding items: outbox in the business transaction; publish after broker ack; restart-safe claiming; bounded retries; harmless duplicates; fixed-text DLQ headers; first-start floor; `unprocessed-record-max-age`; partition key; produced events match the contract schemas.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | Medium | Interrupt during a database-outage hold at shutdown dead-letters a valid event and commits past it | **Fixed.** Hold sleeps through interrupts; record stays unacknowledged and is redelivered |
| 2 | Medium | Runbook replay reaches every consumer group on shared topics; console producer not byte-exact | **Fixed** (group-scoped replay channel; runbook rewritten) |
| 3 | Medium | "Lower the floor to re-notify" does nothing: offsets already committed | **Fixed** in runbook (scale to 0 via PR, group offset reset, lower floor; each approved) |
| 4 | Medium | Missing DLQ topic: auto-create with wrong shape or a stalled channel | **Fixed.** Startup fails when Kafka is reachable and the topic is missing; delivery order unchanged (O-1) |
| 5 | Low | One bad (non-poison) event blocks its topic ~7 min | **Recorded.** Kept 20 attempts as inventory-service did, so a transient error does not dead-letter a good event quickly; documented |
| 6 | Low | Batch outlives lease | **Fixed** |
| 7 | Low | DLQ keys not byte-exact (String round trip) | **Fixed.** ByteArray key deserializer and DLQ key serializer |
| 8 | Low | No ordering across the two input topics | **Recorded** as accepted limitation |
| I | Info | Outbox retries a permanent RecordTooLarge forever | **Recorded**; payloads are a few hundred bytes |
