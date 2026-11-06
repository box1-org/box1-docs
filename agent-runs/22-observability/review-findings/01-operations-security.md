# Review pass 01: operations and security (fresh subagent, 2026-11-06)

Inputs: the diffs of box1-gitops#82 and box1-workloads-dev#119, issue #22, the upstream tempo-operator v0.22.0 source and CRD, Quarkus 3.40.1 source, and `oc auth can-i --as` for the Argo controller service account.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | blocker | `quarkus.otel.traces.exporter` (and the sampler) is BUILD_AND_RUN_TIME_FIXED, so an env override cannot enable export. Confirmed locally with `javap` on quarkus-opentelemetry 3.40.1.1: `TracesBuildConfig` has `exporter` and `sampler`; the run-time config has only `samplerArg`. | Fixed: seven service PRs build in `cdi` plus `traceidratio` at 0.0 (decision 006). #119 now sets `QUARKUS_OTEL_TRACES_SAMPLER_ARG=1.0`. |
| 2 | blocker | The Namespace was in wave 0 while the Role and RoleBinding were in wave -1, so the first sync would fail. | Fixed: Namespace moved to wave -2. |
| 3 | major | No collector metrics, so dropped spans would not be visible. | Fixed: `spec.observability.metrics.enableMetrics: true`; metric name corrected to `_total`. |
| 4 | major | UWM retention and PVC are not sized. | Deferred explicitly in the README and decision 004. Needs `user-workload-monitoring-config` after UWM creates its namespace. |
| 5 | minor | The router and UWM could reach all Tempo ports. | Fixed: router limited to 8443 (OAuth proxy), UWM to 3200. |
| 6 | minor | Unauthenticated OTLP ingest from any namespace. | Accepted for the lab and documented in the NetworkPolicy and PR. |
| 7 | minor | Version and unit wording. | Fixed: queue unit is requests. The `redhat-operators` source offers OTel v0.158; v0.152 is in `redhat-operators-v422`. |
| 8 | info | Argo controller rights are adequate; Tempo labels, ports and fields match v0.22.0; no secrets. | None needed. |
