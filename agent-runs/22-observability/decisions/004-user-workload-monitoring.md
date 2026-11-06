# 004 User-workload monitoring

**Decision:** enable OpenShift user-workload monitoring through a GitOps-managed `cluster-monitoring-config` (`enableUserWorkload: true`), so business metrics and PrometheusRules use built-in monitoring rather than a second Prometheus.

UWM retention and persistence stay at OpenShift defaults (no `user-workload-monitoring-config`) until the namespace exists and usage is measured. Argo now owns `cluster-monitoring-config`, which did not exist before.
