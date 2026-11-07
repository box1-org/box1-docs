# Operations pass (phase 5)

Reviewer: a fresh subagent given the diff `61bcb8c..bed8e44` and the deployed workload, compared with notification-service and operations-console, using read-only `oc get`. It ran `./mvnw -q test` (exit 0). Date: 2026-11-06 EST.

**Confirmed sound:**
- Readiness and liveness are independent of Kafka and the model. Keycloak does not block startup.
- Metric labels are bounded.
- Blocking work runs on worker threads, and the Kafka handler does little.
- Duplicates during a rollout are deduplicated.
- The default URLs resolve to existing Services.

## Service code

| # | Severity | Finding | Disposition |
|---|---|---|---|
| O-1 | medium | Trace and log correlation breaks at the worker pool. The JDK `HttpClient` creates no spans and sends no `traceparent` | **Repaired in `0cf2604`.** Repair: carry the OTel context into the worker, open an `aiops.analysis` span with the `analysisId` attribute, put `analysisId` in MDC, and inject W3C `traceparent` on upstream and model calls (same as A-6) |
| O-2 | low | Upstream body read has no deadline | Same as S-1, repaired |
| O-3 | low | `shutdownNow()` drops queued work silently | **Repaired in `0cf2604`.** Repair: log the count of dropped tasks and count them as `status=ABANDONED` |
| O-4 | low | A FAILED analysis cannot be diagnosed, because only the exception class is logged | **Repaired in `0cf2604`.** Repair: log the class plus the top `org.box1` stack frame, never the message |
| O-5 | low | The runbook is imprecise: lag metric name, group lag meaningless, duration tag, unmeasured refill time, not scraped yet | **Repaired in `0cf2604`** (runbook). The refill time is measured in phase 7 |

## Needed in the box1-workloads-dev runtime PR

| # | Severity | Finding | Disposition |
|---|---|---|---|
| WR-1 | medium | No ServiceMonitor or PrometheusRule | In the runtime PR: copy them from notification-service and add aiops rules |
| WR-2 | medium | The image is still the template, and calls need the Keycloak clients | Order: Keycloak PR, then service merge and promotion |
| WR-3 | low | OTel resource attributes and sampler are missing, and runtime URLs are not explicit | In the runtime PR: set them as Deployment `env` (not ConfigMap literals) |
| WR-4 | info | Probes, port and resources are OK | Measure with `oc adm top` during the first 6h replay before changing anything |
