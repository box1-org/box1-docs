# Phase 6/7: platform delivery and checks (2026-11-06, America/New_York)

User approval (in chat, 2026-11-06): "Yes, merge and sync". This covered merging box1-gitops#82 and syncing the operators, user-workload monitoring, then tracing. It did not cover the service PRs or box1-workloads-dev#119.

## Delivery
- box1-gitops#82 was merged at head `ec0cccc` (checks `box1-phase1-smoke` and `box1-onboarding-plugin-guard` passed). Merge commit: `acc6ce530cab045f42afde85d7f1ace8bf994dc4`.
- Each Argo sync was triggered by setting the Application `operation` at revision `acc6ce5`, about 15:03–15:06 EST. All three reported `Succeeded` and are now `Synced`/`Healthy`.
- The InstallPlans were checked before approval. Each installed only its expected CSV:
  - `install-9flnt` → `tempo-operator.v0.22.0-5`
  - `install-hfrr5` → `opentelemetry-operator.v0.158.0-202611041238`
  Both CSVs reached `Succeeded`, and the CRDs `tempomonolithics.tempo.grafana.com` and `opentelemetrycollectors.opentelemetry.io` were created.
- User-workload monitoring: `prometheus-operator`, `prometheus-user-workload-0` and `thanos-ruler-user-workload-0` are Running. ClusterOperator `monitoring` stayed Available=True, Degraded=False.
- Tracing:
  - TempoMonolithic `box1` is `Ready=True`.
  - Pod `tempo-box1-0` has 4/4 containers ready and 0 restarts.
  - PVC `tempo-storage-tempo-box1-0` is Bound, 10Gi on `lvms-vg1`.
  - `box1-collector` is 1/1 Running. The operator's admission webhook accepted its config.
  - The operator created a ServiceMonitor `box1-monitoring-collector` and an extra ingress NetworkPolicy `box1-collector-networkpolicy`.

## Checks
| Check | Expected | Observed |
|---|---|---|
| Synthetic OTLP/HTTP span sent to the collector (via port-forward), trace `41687357342fbb7816a567659e0a4b5c` | Readable from Tempo | POST returned 200. The first read about 3 s later was empty (the collector reconnects with backoff and batches). A re-read returned the span `smoke-test` with `service.name=box1-trace-smoke`. |
| Collector metrics in UWM (thanos-querier) | Accepted and sent counters | `otelcol_receiver_accepted_spans{receiver=otlp}=1` and `otelcol_exporter_sent_spans{exporter=otlp/tempo}=1`. **The metric names have no `_total` suffix.** |
| Anonymous request to the Jaeger UI Route | Rejected | 403 with the OpenShift OAuth "Log In" page |
| `tempo-box1:3200` (query API) from an order-service-dev pod | Blocked | Timed out (curl 000) |
| `tempo-box1:4317` from an order-service-dev pod | Blocked | Timed out |
| Collector `:4318` from an order-service-dev pod | Reachable | 200 |

At startup the collector logged "connection refused" to `tempo-box1:4317` for about 30 s (20:05:44–20:06:11Z), until Tempo listened. It then connected without intervention.

## Resource use (oc adm top, shortly after start, essentially idle)
| Pod | CPU | Memory |
|---|---|---|
| tempo-box1-0 (4 containers) | 69m | 67Mi |
| box1-collector | 1m | 30Mi |
| prometheus-user-workload-0 | 13m | 189Mi |
| thanos-ruler-user-workload-0 | 2m | 76Mi |
| prometheus-operator (UWM) | 2m | 95Mi |

Node memory went from 59% (75,988 Mi, discovery) to 62% (79,644 Mi). Other workloads also changed in between, so this is not an isolated measurement.

## Differences from source
- The Route termination is `reencrypt`. Git says `edge`; the operator uses reencrypt for the OAuth proxy.
- The collector warns: "otlp alias is deprecated; use otlp_grpc".
- The README and PR name the drop metric `otelcol_exporter_send_failed_spans_total`. The live name has no `_total` suffix.

## Not done
No application traces yet: the service image PRs and box1-workloads-dev#119 are unmerged. No fault scenarios have been run.
