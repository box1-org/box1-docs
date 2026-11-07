# 003 Kiali — proposed

- A `Kiali` CR in `istio-system`, managed by Argo.
- `auth.strategy: openshift`; anonymous access is rejected.
- `deployment.cluster_wide_access: false`, with `deployment.discovery_selectors` matching `istio-discovery: enabled` (`istio-system`, `ztunnel` and the seven service namespaces).
- **Metrics:** `external_services.prometheus` points at `thanos-querier.openshift-monitoring.svc:9091` with the Kiali service-account token. That needs a `cluster-monitoring-view` binding, which is a **new permission → approval**.
- **Ztunnel and waypoint metrics:**
  - a PodMonitor in `ztunnel`, scraped by user-workload monitoring, since `ztunnel` is not an `openshift-*` namespace;
  - a PodMonitor per waypoint namespace;
  - a `Telemetry` in `istio-system` with the `prometheus` metrics provider.
- **Tracing:** `external_services.tracing` uses the Tempo gateway `https://tempo-box1-gateway.box1-observability.svc:8080/api/traces/v1/dev/tempo` (the exact path is to be confirmed against the #22 gateway), `use_grpc: false` and a bearer token.
  - Kiali's service account needs ClusterRole `box1-traces-read-dev` (**new permission → approval**).
  - The `box1-observability` NetworkPolicies must admit Kiali.
- **OSSM console plugin (OSSMC):** not in scope; Kiali gets its own Route.
