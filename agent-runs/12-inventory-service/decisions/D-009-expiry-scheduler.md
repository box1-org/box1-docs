# D-009 Expiry scheduler

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **Clock:** an injected `java.time.Clock` is the only time source for `expires_at`, for choosing due holds and for `expiredAt`. Tests substitute a controllable clock. Outbox claim and retry times stay on the database clock, and the two never get compared, which avoids Order's clock-domain defect.
- **Cadence and batch:** every `INVENTORY_EXPIRY_INTERVAL` (default 5 s), up to `INVENTORY_EXPIRY_BATCH` (default 100) holds, oldest first, with no overlap on one instance.
- **Transaction:** one per hold: `UPDATE reservations SET status='EXPIRED' WHERE id=? AND status='ACTIVE' AND expires_at <= ?`, then the stock decrement, history and outbox row. A failure affects only that hold.
- **Restarts and rollout:** crashing mid-batch loses nothing, since uncommitted holds stay due. Two pods during a rolling update are safe, because the conditional update lets exactly one succeed and the unique outbox index backs it up.
- **Gate, added in Phase 5:** `ExpiryGate` holds expiry for `INVENTORY_EXPIRY_GRACE` (default `PT2M`) after startup, during and after a consumer retry, after an event older than `PT30S`, and while the broker has not answered. Reviewers showed recovery otherwise systematically favors expiry over an unread signal. A held hold only keeps its units longer. The time source is the same clock.
- **Limit:** a reservation that stays unpublished past its `expiresAt` still goes to `EXCEPTION`, by Order's rule.
