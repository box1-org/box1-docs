# Checkpoint: #22 observability (frontier)

Updated 2026-11-06T14:55:54-05:00.

## Phase
Updated 2026-11-06T15:53:13-05:00. Phase 7 is partial. **The first acceptance criterion is live_verified**: a sample orderId leads, through logs and Tempo, to one trace across order, inventory and fulfillment-adapter (`evidence/phase7-order-service-trace.md`). The other criteria are open.

## Done
- Phase 0 discovery: `evidence/phase0-discovery.md` (read-only).
- Design decisions: `decisions/001`–`006`.
- box1-gitops PR [#82](https://github.com/box1-org/box1-gitops/pull/82), branch `observability-tracing-platform` @ ec0cccc. Adds:
  - the Tempo and OTel operators (manual InstallPlans);
  - TempoMonolithic on a 10 Gi PV with 72 h retention;
  - the collector, NetworkPolicies, and UWM enablement.
  All three Applications are manual-sync.
- Seven service PRs (branch `trace-export-build`) build in OTLP export at sampler ratio 0.0: order-service#6, inventory-service#4, fulfillment-adapter#4, notification-service#2, asset-service#4, scenario-controller#3, operations-console#8.
- box1-workloads-dev PR [#119](https://github.com/box1-org/box1-workloads-dev/pull/119) (draft), branch `observability-trace-export` @ 815709d. Sets the sampler arg to 1.0 and the collector endpoint.
- Review pass 01 recorded. Its blockers and majors are fixed, except UWM sizing, which is deferred and documented.

## Tests
- order-service: `./mvnw -B test` passed (28 tests). `package` produced the OTLP `SpanExporter` bean.
- The other six services: not built locally; they rely on PR checks.
- Manifests: `oc kustomize` renders all paths. Server dry run passed for the Namespaces, Subscriptions and ConfigMap. The Tempo and OTel CRs cannot be dry-run before the operators exist.

## Approvals
1–4. Done: platform merged and synced (box1-gitops#82, `acc6ce5`).
5. Done: seven service PRs merged. Builds succeeded. Promotions merged for order, inventory, scenario-controller and operations-console. **Promotion failed** for fulfillment-adapter (#122), notification (#123) and asset (#126): PaC cancelled their checks during seven concurrent promotions. Those PRs are open; nothing was retried.
6. Done for order-service only: box1-workloads-dev#119 merged as `b8513c1`, per the user's "just the order-service for now".
7. Pending: box1-gitops#83 (tidy-up; syncing it restarts the collector).

## Achievement log
`achievements/2026/2026-11-06-observability-tracing-metrics.md` is in box1-docs#94. It is **not merged**: the merge needs explicit user approval. Status comments were posted on #22, #61 and #64.

## Exact next action (updated 2026-11-06T17:39:19-05:00)
**Metrics, alerts and dashboard are live:** box1-workloads-dev#138 (`210c25f`) and box1-gitops#90 (`6988746`); evidence `evidence/phase6-metrics-alerts-dashboard.md`.
- All 7 services are scraped and all dashboard panels have data.
- `Box1OrdersStuck` is firing in Alertmanager on 2 pre-existing stuck orders.
- The AUTO acknowledgement baseline is 5–7 s.

**Criterion 2 is still open.** On 2026-11-06 the user answered "Not now" to the ERP MANUAL-mode latency test; ask again before running it. It **needs user approval for fault injection** (a MANUAL-mode or stalled ERP) to measure:
- `Box1ErpAcknowledgementDelayed` latency against the under-2-minute target;
- `Box1ErpAwaitingOperator` latency.

**Waiting on the user:**
- Look at the dashboard in the console.
- Decide what to do about the 2 stuck orders.

**Done:** the adapter gauge now excludes NEEDS_ATTENTION. fulfillment-adapter#6 (`f1df453`) is released and live; see the metrics evidence.

**Housekeeping:** close #126; two stranded Pending validate runs.

## Open risks
- Vendor support on OpenShift 5.0.0-rc.7 is not established.
- The adapter's Kafka consumer creates no span (decision 005).
- UWM uses emptyDir and default retention.
- OTLP ingest is unauthenticated (lab).

## Next slices after tracing
ServiceMonitors and business-metric alerts (ERP backlog/slowdown); dashboards; deployment overlay; JSON log field audit.
