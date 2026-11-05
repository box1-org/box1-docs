# D-004 Rates, caps and server-side enforcement

**Status:** decided by the agent, Phase 1. Numbers are lab starting points; Phase 4 records measured cost.

## Limits (all configurable; the hard maximums are compiled in and config can only lower them)

| Limit | Default | Hard maximum | Enforced where |
|---|---|---|---|
| Shared ingestion rate (API + load + chaos) | 100 readings/s | 200 readings/s | `IngestionPipeline` token bucket; excess gets 429 / counted `rejected{reason=rate}` |
| Load run rate (sites x assets x metrics x rate per asset) | 5 readings/s | 50 readings/s | validated at arm and start; generator paces to it |
| Sites per run | 2 | 5 | arm |
| Assets per site | 3 | 20 | arm |
| Metrics per run | allowed set only | 4 | arm |
| Rate per asset | 1 / s | 5 / s | arm |
| Run duration | 2 min | 15 min | arm; generator stops at deadline |
| TTL auto-stop | duration + 30 s | 15 min 30 s | server timer independent of any browser; lease heartbeat |
| Concurrent active runs | 1 | 2 | start, under a lock |
| Armed-but-unstarted lifetime | 60 s | 60 s | start rejects an expired arm |
| Chaos burst multiplier | 3x | 5x, still under the shared ingestion cap | chaos executor |
| Producer queue | 2000 records | 5000 | bounded queue; full gives 503 Retry-After / counted `rejected{reason=backpressure}` |
| Producer pause (chaos) | 10 s | 30 s | chaos executor, auto-resume timer |

Requests that bypass the page hit the same checks: the page only renders limits it reads from `GET /api/v1/control/limits`.

## Rationale

The node is at 67% CPU and 64% memory requested. The pod keeps the template's 100m/256Mi request and 1 CPU/512Mi limit unless Phase 4 measurement says otherwise. Kafka is one broker with RF 1, and PostgreSQL is one pod on a 5Gi volume (if D-014 allows a database). 100 readings/s is ~360k rows/hour, which D-009 retention keeps bounded.
