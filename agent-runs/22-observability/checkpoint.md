# Checkpoint: #22 observability (frontier)

Updated 2026-11-06T14:55:54-05:00.

## Phase
Phase 5 (review) is complete for the first vertical slice: tracing platform and trace export. The run is **stopped at the approval boundary**. Nothing has been applied to the cluster.

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

## Approvals needed (in order)
1. Merge box1-gitops#82. This creates three manual-sync Applications only.
2. Sync `observability-operators` and approve the two InstallPlans.
3. Sync `user-workload-monitoring` (enables UWM).
4. Sync `observability-tracing` (creates a 10 Gi PVC and the Tempo, collector and UI pods).
5. Merge the seven service PRs. Each merge triggers a build and dev promotion; export stays off.
6. Merge box1-workloads-dev#119 (turns export on).

## Exact next action
After approval 1–4: verify the CSVs are `Succeeded`, TempoMonolithic is `Ready`, the PVC is bound, and the collector is running. Then check the collector config and NetworkPolicy behaviour. After 5–6: POST a sample order and find its trace in the Jaeger UI across order, inventory and adapter. Record evidence. Then start Phase 4 fault scenarios (Tempo pod restart; collector scaled to 0). Fault injection needs its own approval.

## Open risks
- Vendor support on OpenShift 5.0.0-rc.7 is not established.
- The adapter's Kafka consumer creates no span (decision 005).
- UWM uses emptyDir and default retention.
- OTLP ingest is unauthenticated (lab).

## Next slices after tracing
ServiceMonitors and business-metric alerts (ERP backlog/slowdown); dashboards; deployment overlay; JSON log field audit.
