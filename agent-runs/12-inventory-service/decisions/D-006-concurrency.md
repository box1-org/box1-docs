# D-006 Concurrency strategy

**Status:** decided by the agent in Phase 1, 2026-11-05.

- READ COMMITTED. `inventory_stock(on_hand, reserved)` with `CHECK (reserved >= 0 AND on_hand >= reserved)`. Available is `on_hand - reserved`.
- Reservation is one conditional statement: `UPDATE ... SET reserved = reserved + q WHERE site_id = ? AND sku = ? AND on_hand - reserved >= q`. PostgreSQL takes the row lock, then re-evaluates the predicate against the committed row, so two final-unit orders serialize and the loser matches 0 rows. No version column, because there is no read-modify-write.
- 0 rows is then classified by a plain read: no site or unavailable site, no stock row, or not enough stock.
- The `CHECK` is the database-level guarantee that available cannot go negative, whatever the code does.
- `reserved` is denormalized for this reason. `box1_inventory_reserved_drift` counts stock rows where it differs from the sum of `ACTIVE` and `COMMITTED` holds, and must stay 0.
- **Retry bound:** the same loop as D-007, 20 attempts. Deadlock (`40P01`) and serialization (`40001`) failures are counted in `box1_inventory_conflict_retries_total`. Each transaction holds at most one stock row, so deadlocks are not expected.
