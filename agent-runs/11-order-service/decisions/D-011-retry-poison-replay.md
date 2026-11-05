# D-011 Retry bounds, poison routing and replay

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **Consumer transient failure (database):** 3 attempts in-process with 200 ms, 400 ms backoff. Then the record goes to the dead-letter topic.
- **Poison (malformed JSON, invalid envelope or payload, unknown type, unknown order):** straight to the dead-letter topic with no retries.
- **Dead-letter topic:** `box1.order.dlq.v1`, via the Kafka connector's dead-letter strategy, which adds cause and source-topic headers. Exception text is kept free of payload data. Metric: `box1_events_consumed_total{outcome="dead_lettered"}`.
- **Replay:** a documented runbook procedure that re-produces a record to its source topic with a cluster-admin Kafka shell, recording who and why. Duplicate-safe via `processed_event`. There is no HTTP replay endpoint, per D-003.
- **Publisher:** retries indefinitely with capped exponential backoff (1 s to 5 min). A committed business event is never discarded. Attempts and age are measurable.
