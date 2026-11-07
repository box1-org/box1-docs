# D-006 shipment.failed.v1 with retryable:true

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Decision:** never emit it. Only `REJECTED` produces `shipment.failed.v1`, with `retryable:false` and the ERP1 reason code.

**Why:** order only notes `retryable:true` and inventory ignores it, so it informs nobody; and needs-attention means transport uncertainty, where the ERP may already have committed a shipment. Needs-attention is visible through the adapter's status API and metrics instead.
