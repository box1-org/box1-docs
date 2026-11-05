# D-014 Database for asset-service while #41 is open

**Status:** OPEN, user decision required. Details of the current credential arrangement were reported to the user directly; this record is a pointer.

## Facts

- `asset-service` was onboarded with PostgreSQL off. `workloads/asset-service/postgres.yaml` is empty and unreferenced; no database, PVC or database Secret exists in `asset-service-dev`.
- The prompt requires an independently owned reading store, and D-007/D-009 put readings, alerts and audit in PostgreSQL.
- Adding a database creates a new credential, which needs approval. box1-docs#41 (Vault) is open and not started.

## Options

1. **Recommended: database manifests in Git, Secret created out of band.** `postgres.yaml` holds PVC, digest-pinned PostgreSQL 15 Deployment, Service and a NetworkPolicy (5432 from the app only), copied from the template pattern without its inline Secret. The Deployment references Secret `asset-service-postgres` by name. The user creates that Secret once with `oc create secret generic` (keys documented, values never recorded). No password in Git; meets #41's "no password in Git for newly generated services" for this service. Argo does not manage the Secret; if it is missing the pods wait in `CreateContainerConfigError`, which is visible and harmless.
2. Template pattern with the inline placeholder Secret in Git, as order and inventory have. Fastest, but repeats the arrangement #41 exists to remove, in a public repository.
3. Wait for #41. Blocks Phase 6 and 7 indefinitely.
