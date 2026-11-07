# D-015 Customer data

**Status:** decided by the agent in Phase 1, 2026-11-05.

`customerId` arrives in `order.placed.v1`. Inventory does not need it, so it is not parsed into a domain object, stored, logged or republished. Dead-letter records hold the original value unchanged, so that topic has the source's sensitivity. Admin subjects are stored as the token's `sub`, an opaque ID, not a name or email.
