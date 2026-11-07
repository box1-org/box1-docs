# 004 Ambient enrollment, Postgres and NetworkPolicy — proposed

**Enrollment:**
- Add `istio.io/dataplane-mode: ambient` and `istio-discovery: enabled` to each `workloads/<service>/namespace.yaml` in `box1-workloads-dev`.
- Order: `operations-console-dev` first (no database), then order and inventory, then the other four.
- Rollback: remove the label in Git; Argo self-heals the namespace.

**Postgres stays enrolled,** so the service → database hop is mTLS. Enrolled peers reach the destination pod on HBONE port **15008**, so every `<service>-postgres` NetworkPolicy must allow:
- TCP 15008 from the service pod, beside 5432;
- the ambient probe SNAT address `169.254.7.127/32`, per the upstream ambient NetworkPolicy guidance.

These NetworkPolicy changes merge **before** the namespace labels. If they are missing, enrollment breaks the database path.

**Peers that are not in the mesh:**
- Kafka (`box1-kafka`): 9092 is open to all.
- The ERP VM: the `legacy-erp-sftp` policy matches the adapter pod by label on 2222. Ztunnel keeps the source pod IP in in-pod mode; verify this in Phase 4.
- Keycloak and the collector: verify in Phase 4.

**Baseline:**
- Keep the per-database ingress policies.
- Add egress allow-lists one namespace at a time: DNS, the API server (where used), Kafka 9092, Postgres, the collector 4317/4318, Keycloak, 15008, and the ERP 2222 for the adapter.
- A default-deny is **approval-required** and is added last.
