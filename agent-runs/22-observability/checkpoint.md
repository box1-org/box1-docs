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

## Exact next action (updated 2026-11-06T16:27:01-05:00)
**Done since the last update:**
- notification promotion #123 merged after a second `/retest`. The first validate run was stranded in `PipelineRunPending`, as in box1-docs#64. notification runs `24dda0f` with export off.
- On user instruction, the box1-docs#80 PRs were merged one at a time, 10 s apart (box1-docs#64): box1-gitops#85, asset-service#5 (after fixing its SecurityTest for the no-database CI build), operations-console#9, then box1-workloads-dev#130. Both releases and promotions (#132, #131) succeeded.
- asset-service now runs `c75b6dc`, which includes the trace-export build, so promotion **#126 is superseded. Close it; do not merge** (it would roll back to `0bfca82`).
- box1-gitops#83 (tidy-up) was merged by someone else as `450a5ce`. `observability-tracing` is manual-sync, so it is not applied yet. Syncing restarts the collector.

**Next:**
- notification export: branch `observability-trace-export-notification` is pushed (`9956f90`); **no PR opened**. Open the PR, merge it, prune the orphan ConfigMap (needs approval), then verify the notification spans in an order trace.
- Then: asset, scenario-controller and operations-console export (ConfigMap only, one at a time, 10 s apart, prune each orphan).
- Then the metrics/alerts slice.

## Open risks
- Vendor support on OpenShift 5.0.0-rc.7 is not established.
- The adapter's Kafka consumer creates no span (decision 005).
- UWM uses emptyDir and default retention.
- OTLP ingest is unauthenticated (lab).

## Next slices after tracing
ServiceMonitors and business-metric alerts (ERP backlog/slowdown); dashboards; deployment overlay; JSON log field audit.
