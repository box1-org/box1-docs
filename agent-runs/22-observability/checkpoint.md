# Checkpoint: #22 observability (frontier)

Updated 2026-11-06T14:55:54-05:00.

## Phase
Updated 2026-11-06T15:28:49-05:00. Phase 7 is partial. order-service exports traces, verified end to end: `evidence/phase7-order-service-trace.md`. The other six services are not exporting. Three of them have stuck promotions.

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

## Exact next action
Wait for the user's choice. One option is to re-run promotion **one service at a time**: inventory (already promoted, needs only its export ConfigMap), then fulfillment-adapter (#122 needs a re-run or a new release), then notification and asset. After each, POST an order and confirm the new service's spans join the trace. Separately, consider a backlog issue for the concurrent-promotion failure (cancelled PaC checks fail the promote task).

## Open risks
- Vendor support on OpenShift 5.0.0-rc.7 is not established.
- The adapter's Kafka consumer creates no span (decision 005).
- UWM uses emptyDir and default retention.
- OTLP ingest is unauthenticated (lab).

## Next slices after tracing
ServiceMonitors and business-metric alerts (ERP backlog/slowdown); dashboards; deployment overlay; JSON log field audit.
