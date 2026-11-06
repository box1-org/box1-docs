# 002 Trace UI and access

**Decision:** Tempo's Jaeger UI Route (edge TLS) behind the operator's OpenShift OAuth proxy, using the default SAR (get pods in `box1-observability`). No Cluster Observability Operator and no gateway multitenancy for now.

**Why:** this needs no extra operator and no collector bearer-token wiring. NetworkPolicy keeps Tempo's query API (3200) unreachable from other namespaces, and ingest is allowed only from the collector.

**Revisit if:** the console Observe → Traces view is wanted (COO distributed-tracing UI plugin; extra operator, needs approval), or if per-tenant RBAC is needed.
