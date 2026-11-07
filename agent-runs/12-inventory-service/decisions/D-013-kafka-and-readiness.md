# D-013 Kafka unavailable and readiness

**Status:** decided by the agent in Phase 1, 2026-11-05.

- PostgreSQL is a readiness dependency. Kafka is not. Reads keep working in a broker outage.
- A broker outage stops consumption; offsets do not move, and processing resumes after it.
- Outcomes committed before the outage stay in the outbox, and are published after it. `box1_outbox_pending` and the oldest-pending age show it.
- Consumer tracing and throttled age settings follow Order: `throttled.unprocessed-record-max-age.ms=-1`, so database retries do not restart the pod.
