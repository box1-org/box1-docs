# D-008 Isolation and locking for concurrent creates

**Status:** decided by the agent in Phase 1, 2026-11-05.

- READ COMMITTED with `INSERT ... ON CONFLICT DO NOTHING` on the idempotency record, first statement in the create transaction.
- A concurrent duplicate blocks on the unique index until the first transaction ends. If that commits, the insert returns 0 rows and the winner's record is read. If it rolled back, the insert succeeds. This covers the transaction-boundary case without serializable retries.
- Event handling locks the order row with `SELECT ... FOR UPDATE`. Dedupe uses `processed_event` with `ON CONFLICT DO NOTHING` in the same transaction.
