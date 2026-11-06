# 007 Console Traces view (COO) with Tempo gateway RBAC; Jaeger UI kept

Supersedes decision 002 in part. Decided 2026-11-06 by the user.

**Trigger:** the Tempo operator now shows "Jaeger UI is deprecated". The user wants the native console experience and asked to keep both UIs.

**Options considered:**
- **Single-tenant:** the console plugin backend queries `tempo-box1:3200` directly. Any console user could read all traces.
- **OpenShift-mode gateway (chosen):** every query goes through the gateway with the user's token, so tenant RBAC applies.

**Decision:**
- **COO and console view:** install the Cluster Observability Operator and the `distributed-tracing` UIPlugin.
- **Tempo:** switch TempoMonolithic `box1` to OpenShift-mode multitenancy with one tenant, `dev`. The Jaeger UI stays, routed through the gateway.
- **Collector:** writes with its service-account token, authorized by ClusterRole `box1-traces-write-dev`.
- **Readers:** need `get` on `tempo.grafana.com/dev/traces`, through ClusterRole `box1-traces-read-dev`, bound per user or group. Cluster admins already have it.

**Evidence:**
- The console plugin source (`pkg/proxy/proxy.go`) routes multi-tenant instances to `https://tempo-<name>-gateway.<ns>.svc:8080/api/traces/v1/<tenant>/tempo`.
- The tempo-operator v0.22.0 webhook allows the Jaeger UI with multitenancy, and the Route targets the gateway (`jaegerui_ingress.go`).
- The upstream e2e `monolithic-multitenancy-openshift` matches this design.

**Consequences:**
- Single-tenant traces written earlier are hidden.
- Tempo's raw API (3200) must stay unreachable from other pods, because it trusts any tenant header.
- The collector's own OTLP ingest is still unauthenticated.

**Delivery:** box1-gitops#87. Merge and each sync need approval.
