# Observability: distributed tracing without object storage, console Traces view, metrics, alerts and dashboard

**Date:** 2026-11-06 (America/New_York)

**Status:** Delivered and live. Acceptance is partial. [box1-docs#22](https://github.com/box1-org/box1-docs/issues/22) stays open: 1 of 5 criteria is ticked, with cluster proof. Criterion 2 (alerts and dashboard) is deployed and its alert path is proven, but the ERP-alert latency test was deferred by the user. The other three criteria were not started.

This was a `frontier` profile run. Its run state, decisions 001–008, evidence and review findings are on branch [`agent-run/22-observability`](https://github.com/box1-org/box1-docs/tree/agent-run/22-observability/agent-runs/22-observability). That branch is not merged.

## Outcome

Box1 has end-to-end distributed tracing, metrics, alerts and a dashboard. **None of it uses object storage.**

- **Traces.** All seven Quarkus services export spans to one OpenTelemetry collector. The collector writes them to Tempo, which stores traces on a 10 Gi PersistentVolume. One order is one trace: order → inventory → fulfillment adapter → notification, across Kafka, and through `shipment.confirmed` after the ERP ships. The ERP hop itself is not traced; it is correlated by `fulfillmentRequestId`.
- **Two trace UIs, both access-controlled.** The OpenShift console has Observe → Traces (Cluster Observability Operator plugin). The Jaeger UI is kept. Both sit behind Tempo's OpenShift-mode gateway, so only users allowed to read tenant `dev` see traces.
- **Logs correlate.** Each service's JSON log lines carry `traceId`, `orderId` and `correlationId` (under `mdc`). An order ID found with `oc logs` leads straight to its trace. **Centralized log storage was deferred** to [#82](https://github.com/box1-org/box1-docs/issues/82), because Loki requires object storage and NooBaa reliability is open ([#43](https://github.com/box1-org/box1-docs/issues/43)).
- **Metrics and alerts.** OpenShift user-workload monitoring scrapes all seven services. PrometheusRules raise ERP, order, inventory and availability alerts into the platform Alertmanager.
- **Dashboard.** The Perses dashboard *Box1 / Order flow and ERP* shows order age, ERP acknowledgement and backlog, adapter errors and pipeline health.

| Item | Value |
|---|---|
| Operators (OLM, manual InstallPlans, GitOps-managed) | Red Hat build of Tempo `tempo-operator.v0.22.0-5`; Red Hat build of OpenTelemetry `opentelemetry-operator.v0.158.0-202611041238`; Cluster Observability Operator `v1.5.5` |
| Trace store | `TempoMonolithic/box1` in `box1-observability`. Backend `pv` (10 Gi on `lvms-vg1`), 72 h retention. OpenShift-mode multitenancy, tenant `dev` |
| Collector | `OpenTelemetryCollector/box1`. OTLP in on `box1-collector.box1-observability.svc:4317`/`4318`; exports to the Tempo gateway with its service-account token |
| Trace UIs | Console Observe → Traces (UIPlugin `distributed-tracing`); Jaeger UI at `https://tempo-box1-jaegerui-box1-observability.apps.ocp.box1.org/api/traces/v1/dev/search` |
| Metrics and alerts | 7 ServiceMonitors and 7 PrometheusRules in the service namespaces (`box1-workloads-dev`), evaluated by user-workload Prometheus (`leaf-prometheus`) |
| Dashboard | PersesDashboard `box1-order-flow` and PersesDatasource `box1-thanos-querier` in `box1-observability` |
| GitOps | `box1-gitops` Applications `observability-operators`, `user-workload-monitoring`, `observability-tracing`, `observability-console` and `observability-dashboards`, all manual-sync; source `platform/observability/` |

## Starting baseline

Observed read-only before any change:
- **Cluster:** OpenShift `5.0.0-rc.7`, single node, 31.5 CPU and about 125 GiB allocatable. `oc adm top` showed 44% CPU and 59% memory.
- **No observability stack:** no tracing, OpenTelemetry, logging or COO operator installed. User-workload monitoring was **off** (no `cluster-monitoring-config`).
- **Storage:** about 90 Gi free on `lvms-vg1`. NooBaa `Ready` on a single `pv-pool` backing store.
- **Services:** all seven had `quarkus-opentelemetry`, but `quarkus.otel.traces.exporter=none`. Event envelopes already carried `traceparent`, and the order, inventory and notification consumers already continued it. The fulfillment-adapter Kafka consumer created no span. Business metrics already existed on `/q/metrics`, but nothing scraped them.
- **Known noise:** asset-service logged per-request `VertxTracer delegate not set` warnings ([#61](https://github.com/box1-org/box1-docs/issues/61)).

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Platform | [box1-gitops#82](https://github.com/box1-org/box1-gitops/pull/82) | `acc6ce5` | Tempo and OTel operators; TempoMonolithic on PV; collector; NetworkPolicies; `cluster-monitoring-config` with `enableUserWorkload: true` |
| Platform | [box1-gitops#83](https://github.com/box1-org/box1-gitops/pull/83) | `450a5ce` | Match live state: `otlp_grpc` exporter, `reencrypt` Route, metric name |
| Platform | [box1-gitops#87](https://github.com/box1-org/box1-gitops/pull/87) | `ec16dc3` | COO and `distributed-tracing` UIPlugin; Tempo OpenShift-mode gateway (tenant `dev`); collector token auth; trace ClusterRoles; narrower NetworkPolicies |
| Platform | [box1-gitops#88](https://github.com/box1-org/box1-gitops/pull/88) | `f6c57b1` | Argo CD controller `create tokenreviews`, required by the Tempo webhook to enable OpenShift tenancy |
| Platform | [box1-gitops#89](https://github.com/box1-org/box1-gitops/pull/89) | `8d215b2` | README: the virt-autopilot-owned `monitoring` UIPlugin |
| Platform | [box1-gitops#90](https://github.com/box1-org/box1-gitops/pull/90) | `6988746` | Perses datasource and `box1-order-flow` dashboard (`observability-dashboards`) |
| Services | order-service [#6](https://github.com/box1-org/order-service/pull/6), inventory-service [#4](https://github.com/box1-org/inventory-service/pull/4), fulfillment-adapter [#4](https://github.com/box1-org/fulfillment-adapter/pull/4), notification-service [#2](https://github.com/box1-org/notification-service/pull/2), asset-service [#4](https://github.com/box1-org/asset-service/pull/4), scenario-controller [#3](https://github.com/box1-org/scenario-controller/pull/3), operations-console [#8](https://github.com/box1-org/operations-console/pull/8) | `64362af`, `646bd02`, `5f1d5fd`, `24dda0f`, `0bfca82`, `23125f8`, `96f4a97` | Build in the OTLP exporter with a `traceidratio` sampler at ratio 0.0 (export off by default) |
| Service | [fulfillment-adapter#5](https://github.com/box1-org/fulfillment-adapter/pull/5) | `efa4f1e` | CONSUMER span for `fulfillment.requested.v1`, parented on the envelope `traceparent` |
| Service | [fulfillment-adapter#6](https://github.com/box1-org/fulfillment-adapter/pull/6) | `f1df453` | ERP-delay age gauges exclude `NEEDS_ATTENTION` rows |
| Runtime | box1-workloads-dev [#119](https://github.com/box1-org/box1-workloads-dev/pull/119), [#127](https://github.com/box1-org/box1-workloads-dev/pull/127), [#128](https://github.com/box1-org/box1-workloads-dev/pull/128), [#133](https://github.com/box1-org/box1-workloads-dev/pull/133), [#134](https://github.com/box1-org/box1-workloads-dev/pull/134), [#135](https://github.com/box1-org/box1-workloads-dev/pull/135), [#136](https://github.com/box1-org/box1-workloads-dev/pull/136) | `b8513c1` … | Export on, one service at a time: `QUARKUS_OTEL_TRACES_SAMPLER_ARG=1.0`, the collector endpoint, `deployment.environment=dev` |
| Runtime | [box1-workloads-dev#138](https://github.com/box1-org/box1-workloads-dev/pull/138) | `210c25f` | 7 ServiceMonitors; PrometheusRules for ERP, order, inventory and availability |
| Promotions | box1-workloads-dev #120–#125, #122, #123, #129, #132, #141 | | Images for the above, through the existing release pipelines |

The user approved each merge and sync in chat.

**Made outside Git, with the user's approval:**
- Argo syncs of the manual-sync Applications. Each was triggered by setting the Application `operation`.
- Operator InstallPlan approvals, after checking each one's CSV: `install-9flnt`, `install-hfrr5`, `install-4btrv`.
- Pruning of orphaned generated ConfigMaps in eight workload Applications. Each was a selective Argo sync naming only the orphan, and only when no running pod used it.

**Decisions with consequences** (records are in the run state's `decisions/`):
- **Traces on a PV, not object storage (001).** TempoMonolithic `pv` backend; `TempoStack` needs object storage. Single replica, no HA; deleting the PVC deletes the traces.
- **Build-time exporter, run-time switch (006).** In Quarkus 3.40, `quarkus.otel.traces.exporter` and the sampler are fixed at build time, so env vars alone could not turn export on. Images build in OTLP export with `traceidratio` at 0.0; the deployment sets the ratio. `quarkus.otel.sdk.disabled` was rejected because it would break envelope `traceparent` values.
- **Gateway RBAC for traces (007).** The console plugin reads single-tenant Tempo with no user check, so Tempo moved behind its OpenShift-mode gateway. Readers need `get` on `tempo.grafana.com/dev`, resourceName `traces` (ClusterRole `box1-traces-read-dev`); cluster admins already have it. Tempo's raw API (3200) trusts any tenant header, so it is closed to other pods.
- **Rules next to their metrics (008).** User-workload rules see only their own namespace, so each PrometheusRule lives with its service. `leaf-prometheus` evaluation avoids Thanos Ruler lag.
- **Perses for the dashboard (008).** It is the console's direction, and OpenShift Virtualization already uses it on this cluster.
- **Logging deferred.** A user decision; tracked in [#82](https://github.com/box1-org/box1-docs/issues/82).

## Validation and evidence

| Test | Expected | Observed |
|---|---|---|
| Synthetic span sent to the collector | Readable from Tempo | 200; span read back |
| Order trace, three services | One connected trace | Order `ord_ebae0171…` (trace `113f8a68…`): 10 unique spans across order, inventory and the adapter's CONSUMER span, each parented on the publishing span; order reached `SHIPPED` |
| Order trace, four services | Notification joins | Order `ord_79c7a107…`: 11 spans, including 4 notification consumer spans |
| orderId → trace through logs | Same `traceId` everywhere | `oc logs` lines in order, inventory and the adapter carry `mdc.traceId`, `orderId` and `correlationId` |
| All seven exporting | Traces per service | TraceQL `{resource.service.name=…}` finds traces for each service; about 18.7 spans/s, mostly asset telemetry |
| Gateway read, authorized | 200 | Through the gateway with the operator's token, tenant `dev`: 200 |
| Gateway read, anonymous | Rejected | 302 to OpenShift login; data paths return "failed to find token" |
| Trace RBAC (SubjectAccessReview) | Least privilege | Collector: create **true**, get **false**. Unrelated service accounts: neither. Operator: get **yes** |
| Console Observe → Traces | Usable | Reported working by the user ("the Traces are working properly") |
| Scraping | 7 targets up | `up` = 1 for all seven |
| Dashboard | Data in all panels | All 17 panel queries return series; datasource and dashboard `Available` |
| Alert path | Rule → Alertmanager | `Box1OrdersStuck` pending, then **firing at 22:38:40Z**, and **active in the platform Alertmanager** |
| Normal AUTO ERP baseline | Well under 30 s | Three orders shipped in 5.2, 7.1 and 7.1 s. `max_over_time(fulfillment_oldest_unacknowledged_seconds[10m])` = 0. No ERP-delay alert |
| Adapter gauge fix | Test catches the bug | With `-Pcontainers` against real PostgreSQL and Kafka: the new assertion **fails on the old SQL** and passes with the fix (8/8). Default `verify`: 111 tests. Live: an order shipped in 8 s; gauges 0 |

**Reviews.** Five same-model reviewer passes, on the platform, gateway, metrics and alerts changes, found real defects before deployment. All were fixed:
- env vars cannot change the build-time exporter;
- a namespace/Role sync-wave ordering failure;
- missing collector metrics;
- Tempo's raw API exposed to user-workload monitoring;
- an over-broad network policy;
- alert latency without margin;
- missing down alerts;
- the adapter gauge counting `NEEDS_ATTENTION` rows.

**Not tested or not established:**
- **ERP-alert latency.** `Box1ErpAcknowledgementDelayed` (worst case about 90 s from acceptance, by design) and `Box1ErpAwaitingOperator` were not measured against the under-2-minute target. That needs a MANUAL-mode or stalled ERP, which is fault injection; the user deferred it.
- **The notification delivery path.** The test order created no notification intent.
- **Outage behaviour:** the collector or Tempo going down while orders flow.
- **Tempo disk growth** over 72 h at the observed span rate.
- **The Perses dashboard rendering in the console.**
- **The `NEEDS_ATTENTION` case of the gauge fix on the cluster.** None exist live.
- **Vendor support** for these operator versions on OpenShift 5.0.0-rc.7.

## Incidents during delivery

- **Seven concurrent releases.** Merging the seven service PRs together made Pipelines as Code cancel the checks on three promotion PRs: fulfillment-adapter #122, notification #123 and asset #126. The promote task treats a cancelled check as failed. The services were brought in **one at a time**, with at least 10 s between merges (#64). #122 and #123 were rescued with `/retest`. #126 was superseded by a later asset promotion and is stale.
- **Stranded check runs (#64).** `box1-gitops-validate-brw2n` and `-5tkqk` stayed in `PipelineRunPending` after GitHub reported them failed. `/retest` produced passing runs. Both stranded runs remain in `box1-ci`.
- **Orphaned ConfigMaps ([#42](https://github.com/box1-org/box1-docs/issues/42) item 2).** Each export change edited a `configMapGenerator`, which orphaned the previous ConfigMap. Workload apps do not prune, so Argo reported OutOfSync and `fulfillment-adapter-release-l769j` failed promote after a correct rollout. The orphans were pruned by name. The permanent fix belongs to #42.
- **Tempo webhook refused Argo.** The first gateway sync failed: the applier must already hold `create tokenreviews`. Tempo stayed single-tenant and ingest continued. [box1-gitops#88](https://github.com/box1-org/box1-gitops/pull/88) granted only that rule, then a two-step sync (Tempo first, then collector and policies) switched over with no send failures. The PVC was kept.
- **An unplanned UIPlugin.** Installing the COO caused OpenShift Virtualization's `virt-platform-autopilot` to create UIPlugin `monitoring` (with Perses). The user chose to keep it, documented in Git ([#89](https://github.com/box1-org/box1-gitops/pull/89)) and not managed by Argo, because the autopilot reconciles it.

## Final operational state

- **Managed by Argo CD from `box1-gitops` `main`** (manual sync): the operators, user-workload monitoring config, Tempo, the collector, trace RBAC, NetworkPolicies, the console UIPlugin and the Perses objects. All are Synced/Healthy.
- **Managed from `box1-workloads-dev` `main`** (auto-sync): service export settings, ServiceMonitors and PrometheusRules.
- **Live versions:** the service images running are those promoted by the PRs above. fulfillment-adapter runs `f1df453`.
- **Expected firing alert:** `Box1OrdersStuck`, on two orders open since about 2026-11-05.
- **Footprint, idle:**
  - Tempo about 136–145 Mi;
  - collector about 40–53 Mi;
  - user-workload monitoring about 360 Mi;
  - COO, plugins and Perses about 220 Mi.
- **Lab limits:**
  - single replica everywhere;
  - user-workload Prometheus on emptyDir with default retention;
  - OTLP ingest to the collector is unauthenticated from any namespace;
  - traces written before the gateway switch are hidden and expire within 72 h.

## Recovery and follow-ups

**To stop exporting:** set `QUARKUS_OTEL_TRACES_SAMPLER_ARG=0.0` (or revert the export PRs). Services keep working, and trace IDs still propagate.

**To remove a layer:** delete its Application with cascade. `platform/observability/README.md` documents each layer and its rollback.
- Reverting the gateway means reverting Tempo, the collector and the policies together. Traces written as `dev` are then hidden.
- The collector, Tempo or Perses going away does not affect orders. Exports are asynchronous and drop spans. This is **not tested** as an outage.

**Open on #22:**
- the ERP-alert latency test (needs approval);
- the deployment SHA/digest overlay;
- the structured-log redaction audit;
- disabling the `operate` profile.

**Related:**
- Centralized logging: [#82](https://github.com/box1-org/box1-docs/issues/82).
- Promotion failure on orphaned ConfigMaps: [#42](https://github.com/box1-org/box1-docs/issues/42).
- Stranded PaC checks: [#64](https://github.com/box1-org/box1-docs/issues/64).
- Per-request `VertxTracer` warnings: [#61](https://github.com/box1-org/box1-docs/issues/61). Gone from six services; **asset-service still logs them**.

**Housekeeping, not done:**
- close the stale promotion box1-workloads-dev#126;
- delete the two stranded PipelineRuns;
- clean up or explain the two stuck orders.

No owner is assigned to these follow-ups. No credentials or tokens are included in this log or the run state.
