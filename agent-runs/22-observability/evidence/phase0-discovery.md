# Phase 0 discovery (read-only, 2026-11-06 America/New_York)

No cluster state was changed. Commands were `oc get`, `oc adm top`, `oc auth can-i`, and `oc apply --dry-run=server` (server-side dry run, no persistence).

## Cluster
- OpenShift `5.0.0-rc.7`, single node `quark.host.box1.org`. Allocatable: 31.5 CPU, about 125 GiB memory. `oc adm top node` showed 14.0 cores (44%) and 75,988 MiB (59%).
- Storage classes: `lvms-vg1` (default, topolvm, WaitForFirstConsumer), with `capacity.topolvm.io/vg1` = 90 GiB free; `openshift-storage.noobaa.io` (OBC).
- NooBaa `Ready`, with one `pv-pool` backing store (`noobaa-default-backing-store`). ODF 4.22.7.
- User-workload monitoring: there was no `cluster-monitoring-config` ConfigMap, and `openshift-user-workload-monitoring` had no pods.
- No Tempo, OpenTelemetry, logging, Loki or Cluster Observability Operator CSV installed. No namespace matched `observ|tempo|otel|tracing`.

## Catalog
| Package | Catalog | stable currentCSV |
|---|---|---|
| tempo-product | redhat-operators | tempo-operator.v0.22.0-5 |
| tempo-product | redhat-operators-v422 | tempo-operator.v0.21.0-3 |
| opentelemetry-product | redhat-operators | opentelemetry-operator.v0.158.0-202611041238 |
| opentelemetry-product | redhat-operators-v422 | opentelemetry-operator.v0.152.0-1 |
| cluster-observability-operator | redhat-operators | v1.5.5 |

The Tempo CSV supports only the AllNamespaces install mode; its suggested namespace is `openshift-tempo-operator`. `TempoMonolithic` `spec.storage.traces.backend` accepts `memory|pv|azure|gcs|s3` (upstream v0.22.0 CRD). The CRD has no retention field, so retention goes in `extraConfig.tempo.compactor.compaction.block_retention`.

## GitOps
- Platform Applications in `box1-gitops/applications/` are manual-sync. Subscriptions use `installPlanApproval: Manual`. `box1-root` auto-syncs Application objects.
- The Argo application controller ClusterRole has cluster-wide read, full `operators.coreos.com`, and `can-i create configmaps -n openshift-monitoring` = yes. Operator CR rights are granted per namespace through a Role, as in `platform/kafka/rbac.yaml`.
- Workload Applications in `box1-workloads-dev` auto-sync with selfHeal. Service runtime config is a kustomize `configMapGenerator`. No service NetworkPolicy restricts egress.

## Services (origin/main)
- All seven Quarkus 3.40.1.1 services include `quarkus-opentelemetry`, `quarkus-micrometer-registry-prometheus` and `quarkus-logging-json`. Each sets `quarkus.otel.{traces,metrics,logs}.exporter=none`.
- The envelope `traceparent` is defined in `box1-ops-contracts/events/v1/envelope.schema.json`. The consumers in order, inventory and notification set the span parent from it. No span links are used anywhere. The fulfillment-adapter Kafka consumer creates no span, and the adapter has no `camel-quarkus-opentelemetry`.
- MDC: `orderId` and `correlationId` are set in some paths. traceId in MDC relies on quarkus-opentelemetry; not verified.
- Business metrics already exist (outbox pending/age, stuck orders, about 30 fulfillment meters, and others) on `/q/metrics`. No ServiceMonitors exist.
