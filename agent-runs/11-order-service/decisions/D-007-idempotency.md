# D-007 Idempotency scope, fingerprint and retention

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **Scope:** `(consumer_scope, idempotency_key)` is unique. `consumer_scope` comes from the optional `X-Consumer-Id` header and defaults to `anonymous`. This is caller-supplied and not an identity, per D-003 and box1-docs#40.
- **Fingerprint:** SHA-256 over the validated `customerId`, `sku`, `quantity` and `siteId`, each length-prefixed, so JSON formatting and field order do not matter.
- **Key limits:** 1 to 255 characters. Stored as sent and never logged.
- **Responses:** first request 201 with Location. Same key and body returns 200 with the same order and `Idempotency-Replayed: true`. Same key and different body returns 409 Problem.
- **Retention:** kept for the life of the order, with no purge in v1. Purging would let an old key create a second order. Size is small and a purge job is a follow-up if measured growth needs one.
