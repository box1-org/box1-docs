# D-008 Database and credential while #41 is open

**Status:** proposed. **A new Secret needs user approval; its value is created by the user out of band.**

- The service was onboarded with PostgreSQL **off**: `workloads/notification-service/postgres.yaml` is empty and no Secret is in Git (observed 2026-11-05 23:36 EST). The template's committed-credential problem tracked in #41 therefore does not exist for this service.
- Follow the asset-service pattern (#15 D-014): add PostgreSQL to `box1-workloads-dev` (Deployment, Service, PVC, NetworkPolicy allowing 5432 only from the service's pods) **with no Secret in Git**. The user creates `notification-service-postgres` once, with keys `POSTGRESQL_DATABASE`, `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`. The service reads the user and password through `secretKeyRef`.
- When #41 lands (Vault), this Secret moves with the other services.
- Flyway runs at start with the runtime login (no separate migration owner yet, as in the other services; `postgres/OWNERSHIP.md` prefers one where supported).
- Persistence is plain JDBC with JTA, as in order-service and inventory-service.
