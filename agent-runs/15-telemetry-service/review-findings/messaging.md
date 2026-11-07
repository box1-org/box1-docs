# Messaging pass

Fresh read-only subagent, given the diffs, prompt, domain contracts and profile; not the implementation reasoning. It also disassembled SmallRye 4.37 jars to check behavior. 2026-11-05 ~19:37 EST.

MSG-1 (medium) `latest` plus partitions without a committed offset: readings answered 202 can be skipped (first deploy; a never-used partition while the pod restarts; offsets expired). SmallRye's throttled strategy commits only processed offsets. Same family as ARCH-4.
MSG-2 (medium) Transient retries are unbounded and the stall detection is off (unprocessed-record-max-age=-1, Kafka readiness off, database UP). @Blocking(ordered=true) means one ordered worker: all six partitions stop, not one. Runbook and Javadoc wording wrong.
MSG-3 (low) Records still queued at shutdown are abandoned: futures never completed, HTTP waits the full ack timeout, load readings uncounted.
MSG-4 (low, contract) A retry after 503 publishes a second record with a new random eventId; consumers that dedupe on eventId (contract invariant 4) double-count. Derive eventId deterministically from the natural key.
MSG-5 (low) Each POST blocks a worker for up to 5 s; ~500 waiting requests can exhaust the shared worker pool, delaying stop-all exactly during a pause.
MSG-6 (low) Outbox lease shorter than a worst-case batch; failures do not stop the batch; per-asset ordering claim in TELEMETRY.md does not hold for alerts. Same family as PERS-6/OPS-5.
MSG-7 (low) Producer pause outlives its run. Same as ARCH-3.
MSG-8 (low, docs) If the DLQ topic is missing, broker auto-create (box1-kafka does not disable it) creates it with defaults; it does not "fail to dead-letter". Runbook wrong.
MSG-9 (info) causationId on readings is a source tag ("ingest:api"), not an ID.
MSG-10 (info) First value for a timestamp wins; state it in the runbook.

Disagreement with ARCH-5/OPS-3: this pass reports from bytecode that an exception thrown from a MANUAL-ack Message method fails the stream without a nack, so shutdown during a retry does not dead-letter. The repair makes the path explicit either way (see outcomes).

Verified OK (reviewer): outbox in the business transaction; publish after broker confirmation; restart-safe claims; 202 after ack with permits released in the callback; poison handling with reason-code-only headers; own threshold events skipped; natural-key dedup in the projection transaction; traceparent continuation; schema and DLQ topic conventions.

## Outcomes (asset-service 7cdc138, contracts 2fe191d)

| Finding | Outcome |
|---|---|
| MSG-1 | Fixed (see ARCH-4). |
| MSG-2 | Fixed in part. Retries stay unbounded for transient errors (no dead-lettering of valid data), but readiness check `projection` goes DOWN after 10 min on one record; wording corrected (one worker stalls all partitions). |
| MSG-3 | Fixed. Queued records complete exceptionally at shutdown and count as `dropped{reason=shutdown}`. |
| MSG-4 | Fixed. Reading eventId = name-based UUID over the natural key. `EventIdTest`. |
| MSG-5 | Fixed. At most 64 requests wait for an ack; above that 503 TOO_MANY_WAITING. |
| MSG-6 | Fixed (see PERS-6); TELEMETRY.md ordering claim narrowed to readings. |
| MSG-7 | Fixed (see ARCH-3). |
| MSG-8 | Fixed in the runbook (auto-create behavior described). Broker-level auto-create is shared infrastructure, not changed. |
| MSG-9 | Documented in TELEMETRY.md. |
| MSG-10 | Documented in the runbook and TELEMETRY.md. |
