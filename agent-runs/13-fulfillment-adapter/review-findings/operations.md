# Operations pass

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| O1 | Medium | An outage could exhaust every request's upload budget, with only per-ID reconcile available | **Fixed.** `POST /internal/fulfillments/reconcile?reason=...` restricted to transport reasons, each request audited; only one attempt per batch is spent while the endpoint is down. Harness check passes. |
| O2 | Medium | Replay instructions were incomplete | **Fixed.** The runbook gives the SQL to find a record, the key (`orderId`), keeping the `eventId` unchanged, and that every replay to a shared topic needs approval. |
| O3 | Medium | A memory request of 256Mi is below the likely steady state | **Open: workloads PR.** Request 384Mi, limit 512Mi; measure after the first deploy. |
| O4 | Low | The readiness probe timeout (2 s) is shorter than pool acquisition (5 s) | **Open: workloads PR.** Probe `timeoutSeconds: 5`. |
| O5 | Low | Gauges go stale silently; publish lag was discarded | **Fixed.** `fulfillment_metrics_refresh_age_seconds` and `fulfillment_outbox_publish_lag`. |
| O6 | Low | Runbook wording for `fulfillment_queued` | **Fixed.** |
| O7 | Low | Retention clock (same as P7) | **Documented.** |
| O8 | Low | No HTTP shutdown drain | **Fixed.** `quarkus.shutdown.timeout=20s`. |
| O9 | Low | The DLQ must exist before Kafka input runs | **Open for the user.** D-009 merge order. |
