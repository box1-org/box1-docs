# D-012 Adapter database

**Status:** resolved 2026-11-05 by the user: option A, approved ("do the merges"; D-009 sync approved separately). See evidence/07-release-live.txt.

**Conflict:** the prompt says `box1-workloads-dev/workloads/fulfillment-adapter/` includes `postgres.yaml` from the template pattern. In fact the adapter was onboarded with PostgreSQL off: `postgres.yaml` is empty and not in the kustomization, and there is no database or database Secret. The adapter cannot be durable without one.

**Options:**
- A (recommended) a workloads PR adding PostgreSQL (PVC, Deployment, Service, NetworkPolicy, as order/inventory) **without** a Secret in Git; the user creates `fulfillment-adapter-postgres` out of band before the merge. Needs approval for the new credential and a check that the workloads validator accepts it.
- B the template pattern, which repeats the weakness tracked in #41.

**Consequences:** Phases 1–5 proceed locally. Phase 6 cannot deploy a working adapter until this is decided.

**Validator check (2026-11-05):** `box1-gitops/platform/pipelines/tasks/gitops-validate.yaml` checks kustomize rendering, digest pinning, required kinds and probes. It does not require an inline Secret, so option A passes validation.

**Option A in detail:**
- `workloads/fulfillment-adapter/postgres.yaml`: PVC 5Gi; Deployment `rhel9/postgresql-15` at the same digest as order and inventory; Service; NetworkPolicy admitting only the adapter on 5432. No Secret.
- The Deployment's `envFrom` references a Secret `fulfillment-adapter-postgres`. The user creates it out of band before merge, with keys `POSTGRESQL_DATABASE=fulfillment_adapter`, `POSTGRESQL_USER=fulfillment_adapter`, `POSTGRESQL_PASSWORD` and `QUARKUS_DATASOURCE_PASSWORD` (the same generated value).
- The adapter Deployment gains `env` entries for the JDBC URL and username, and `envFrom` the same Secret.
