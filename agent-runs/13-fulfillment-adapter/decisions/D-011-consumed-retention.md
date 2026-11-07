# D-011 Retention for consumed/ files

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Decision:** the adapter deletes its own `consumed/` files older than 7 days (`FULFILLMENT_CONSUMED_RETENTION`, default `P7D`), matching the ERP's purge. The database keeps the exact bytes of every result and quarantined file, so `consumed/` is a courtesy copy, not a record.
