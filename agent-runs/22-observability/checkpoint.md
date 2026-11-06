# Checkpoint: #22 observability (frontier)

Updated 2026-11-06T14:55:54-05:00.

## Phase
Updated 2026-11-06T15:09:07-05:00. The platform part of Phase 6 (GitOps delivery) is done and checked live: `evidence/phase6-platform-delivery.md`. The run is **stopped at the next approval boundary**: the service PRs and the export switch-on.

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
1. ~~Merge box1-gitops#82~~: merged as `acc6ce5`.
2. ~~Sync `observability-operators` and approve the InstallPlans~~: Tempo v0.22.0-5 and OTel v0.158.0 are `Succeeded`.
3. ~~Sync `user-workload-monitoring`~~: running.
4. ~~Sync `observability-tracing`~~: Tempo is `Ready`, the PVC is bound, the collector is running. Smoke span, OAuth and NetworkPolicy checks passed.
5. **Pending:** merge the seven service PRs. All checks pass; each merge builds and promotes to dev, with export still off.
6. **Pending:** merge box1-workloads-dev#119, which turns export on. Mark it ready first.
7. **Pending:** merge and sync box1-gitops#83 (tidy-up). Syncing restarts the collector.

## Exact next action
After 5 and 6: confirm each service runs the new digest and logs no exporter errors. Check that #61's VertxTracer warnings are gone. POST a sample order, find its trace by traceId (from the JSON log or the order record) in Tempo, and confirm spans from order, inventory and the adapter. Record evidence and measure span rate and PV growth. Then do Phase 4 fault scenarios: a Tempo pod restart keeps traces; the collector scaled to 0 leaves orders working. Fault injection needs separate approval.

## Open risks
- Vendor support on OpenShift 5.0.0-rc.7 is not established.
- The adapter's Kafka consumer creates no span (decision 005).
- UWM uses emptyDir and default retention.
- OTLP ingest is unauthenticated (lab).

## Next slices after tracing
ServiceMonitors and business-metric alerts (ERP backlog/slowdown); dashboards; deployment overlay; JSON log field audit.
