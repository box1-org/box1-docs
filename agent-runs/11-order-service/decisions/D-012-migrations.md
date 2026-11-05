# D-012 Migration ownership and compatibility

**Status:** decided by the agent in Phase 1, 2026-11-05.

- The service owns its Flyway migrations at `src/main/resources/db/migration/`, applied at startup before ready.
- Baseline `V1__order_schema.sql` creates all five tables. The contracts fixture stays a minimal example, per `MIGRATIONS.md`.
- One login (`order_service`) runs migrations and queries, since the deployment has one. D-004 keeps the names. The separate migration owner in `OWNERSHIP.md` applies "when the deployment supports it" and would need another credential, so it is a recorded limitation to revisit with D-016.
- Rollback is forward-only with a corrective migration. Applied migrations are immutable.
- The target database holds no order data today. `order_state_history` rejects UPDATE and DELETE with a trigger.
