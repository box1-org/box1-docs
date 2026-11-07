# Architecture pass

Fresh read-only subagent, given the diffs, prompt, domain contracts and profile; not the implementation reasoning. 2026-11-05 ~19:32 EST.

ARCH-1 (medium) Accepted future timestamps (up to +5 min) push alert_state.last_measured_at ahead, so correctly timed readings are not evaluated for minutes; CLOCK_SKEW draws +2..+10 min and the catalog text claims all of those are rejected (only >+5 min are). Same as PERS-1, found independently.
ARCH-2 (medium) The per-run rate cap checks only baseRate; BURST multiplies it up to 5x (250/s on a 50/s run) and runs can consume the shared 100/s bucket, starving real API writers. Prompt: every run has a maximum rate enforced by the server.
ARCH-3 (medium) A producer pause can outlast its run: stop of one run, COMPLETED and EXPIRED never resume the producer; only stop-all/reset do. All ingestion paused up to 30 s with no run shown.
ARCH-4 (low) auto.offset.reset=latest can skip readings already acknowledged with 202 (first deploy before assignment; offsets expired after long downtime).
ARCH-5 (low) Shutdown during a transient database retry rethrows, the message is nacked and a valid reading is dead-lettered.
ARCH-6 (low) Natural-key dedup silently drops a corrected retry; OUT_OF_ORDER blocks cut by the injection end collide with later normal readings.
ARCH-7 (low) stop-all racing start can leave a run emitting until the next heartbeat. Same as PERS-2.
ARCH-8 (low) alert_state and asset_last_seen grow without bound. Same as PERS-5.
ARCH-9 (low) arm writes the run and its ARM audit in separate transactions. Same as PERS-7.
ARCH-10 (info) No machine identity can obtain telemetry-writer (public client only); real ingestion through the Route cannot be exercised end to end. Follow-up needing approval.
ARCH-11 (info) Only activation emits an event; clear/escalation are database-only. Documented in TELEMETRY.md.
ARCH-12 (info) Seed replay reproduces what was generated, not what was ingested (rate limit, backpressure).
ARCH-13 (info) Load runs are not gated by namespace; control.enabled defaults true.

Verified OK (reviewer): service owns its state, no cross-service reads; no distributed transaction; 202-after-ack and bounded in-flight; explicit transitions with guarded updates and advisory lock; server-side enforcement of caps, gate, confirmation; restart safety; chaos telemetry-only; stable keyset pagination; scope creep small (/preview, /reset).

## Outcomes (asset-service 7cdc138, workloads bb0bcae, gitops b313754, contracts 2fe191d)

| Finding | Outcome |
|---|---|
| ARCH-1 | Fixed. Consumer stores but does not evaluate readings >5 min ahead; watermark clamped to the clock; chaos forward skew +6..+10 min, catalog text corrected. Test `anAcceptedFutureTimestampDoesNotSuspendLaterAlerts`, `RunScriptTest` skew bound. |
| ARCH-2 | Fixed. Per-run token bucket at the run cap (bursts included); runs together at most half the shared rate. Scenario `burst`. |
| ARCH-3 | Fixed. Pause length bounded by the run's remaining time; the run that paused resumes the producer when it ends. Test `aProducerPauseNeverOutlivesItsRun...`. |
| ARCH-4 | Fixed. `earliest`; readings older than retention skipped (counted), not dead-lettered. D-010 amended. |
| ARCH-5 | Fixed. Shutdown mid-retry returns an uncompleted stage (no ack, no nack). Messaging pass disputes the original risk; fix is safe either way. |
| ARCH-6 | Fixed. Conflicts counted and logged as `duplicates{kind=different_value}`; out-of-order shuffle stays within the injection; first-value-wins documented. |
| ARCH-7 | Fixed. Start-and-launch and stop-all serialized by a pod-local lock. |
| ARCH-8 | Fixed. Retention prunes `asset_last_seen` and inactive `alert_state`. Test in `RetentionTest`. |
| ARCH-9 | Fixed. `RunTransitions.arm` is one transaction. |
| ARCH-10 | Recorded. A machine client for `telemetry-writer` needs a new credential and approval; follow-up. |
| ARCH-11 | No change: TELEMETRY.md states only activation is an event. |
| ARCH-12 | Documented in the runbook's Known limits. |
| ARCH-13 | Fixed. `ASSET_CONTROL_ENABLED` defaults false; the dev Deployment sets true. |
