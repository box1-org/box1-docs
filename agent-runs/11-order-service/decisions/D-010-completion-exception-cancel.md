# D-010 COMPLETED, EXCEPTION and CANCELLED

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **COMPLETED:** `ORDER_COMPLETION_POLICY=none|on-shipment`. Default `none`, so SHIPPED is where an order rests until a real completion signal exists. `on-shipment` completes in the shipment transaction.
- **EXCEPTION:** the three cases in D-009. Means manual reconciliation is required. No reconciliation tooling is in scope.
- **CANCELLED:** legal only from SUBMITTED, since no stock is held. The state machine enforces this, but **no cancel endpoint is exposed**. The prompt defines none, and an unauthenticated public cancel is unacceptable under D-003.
