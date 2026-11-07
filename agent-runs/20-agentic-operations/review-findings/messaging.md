# Messaging pass (phase 5)

Reviewer: a fresh subagent given the diff `61bcb8c..bed8e44`, the prompt, the contracts, notification-service's configuration and the live KafkaTopics. It made no changes and did not run tests. Date: 2026-11-06 EST.

**Confirmed sound:**
- No offset commits (`enable.auto.commit=false`, `commit-strategy=ignore`).
- Nothing produced, and no DLQ settings.
- Readiness is independent of Kafka.
- Poison records are acked and counted, so they don't block a partition.
- Duplicates are harmless.
- Window state changes hold the lock.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| M-1 | medium | Consumer group `agentic-operations` is not declared in `TOPICS.md` (phase 2 gate) | Already planned as the contracts PR (Q-7). Not repaired in code. |
| M-2 | medium | A fixed group shared across pods or environments splits partitions, so each pod's window is partial | **Repaired in `0cf2604`.** Repair: the group ID comes from `AIOPS_CONSUMER_GROUP` (default `agentic-operations`). One replica is documented as a hard constraint. Per-environment groups go in the contracts PR. |
| M-3 | low/medium | There is no correlationId index, though the javadoc claims one and the prompt asks for it | **Repaired in `0cf2604`.** Repair: add a correlation index with the same eviction, accept it in `list_recent_events`, and fix the javadoc. |
| M-4 | low | Arrival-order pruning keeps expired events counted, and the oldest-age gauge is skewed | **Repaired in `0cf2604`.** Repair: compute the oldest age by scan and prune by scan. Query results were already filtered by cutoff. |
| M-5 | low | Envelope validation skips `schemaVersion` and `causationId` | **Repaired in `0cf2604`.** Repair: check `schemaVersion == 1` and that `causationId` is 1–128 characters. Full per-type schema validation stays out of scope; the payload is reduced to bounded scalars. |
| M-6 | low | A failed start seek is silent and untested | **Repaired in `0cf2604`.** Repair: catch, log a WARN, count `aiops_window_seek_failures_total`, and add a unit test with MockConsumer. |
| M-7 | low | O(n) removal under the lock with 20,000 events | Accepted: bounded, and the window is fine at lab volumes. Revisit if `aiops_window_events` stays near the cap. |
