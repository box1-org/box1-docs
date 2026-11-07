# D-004 Delivery worker, retry limits and provider outcome classes

**Status:** decided by the run.

## Statuses

`PENDING` (no attempt yet) → `RETRY_SCHEDULED` → `DELIVERED` | `FAILED`. Terminal states never change.

## Worker

- A scheduled worker claims due intents (`status IN (PENDING, RETRY_SCHEDULED) AND next_attempt_at <= now()`) with `FOR UPDATE SKIP LOCKED`, sets a lease (`claimed_until = now() + 30 s`), and commits. Database time only.
- The provider is called outside any transaction with a 2 s timeout and `notificationId` as the idempotency key.
- The attempt row, the new status and (on a terminal status) the outbox row are written in one transaction, guarded by the lease owner, so a stale worker cannot overwrite a newer result.
- Shutdown: the worker stops claiming. An in-flight call completes or its lease expires; the next start resumes from the database. A crash after a successful provider call but before the commit repeats the call, and the stub returns the same receipt (D-003).

## Limits

- At most **6 attempts** per intent. Backoff before attempt *n+1* is `min(2 s × 2^(n−1), 60 s)`: 2, 4, 8, 16, 32 s, about one minute in total. No jitter (one replica).
- Configurable downward only: `NOTIFY_DELIVERY_MAX_ATTEMPTS` ≤ 10, `NOTIFY_DELIVERY_MAX_BACKOFF` ≤ 5 min. Larger values fail startup.

## Outcome classes

| Provider result | Class | Effect |
|---|---|---|
| 2xx with receipt | success | `DELIVERED` |
| 500, 502, 503, 504, 408, 429, timeout, connection error | transient | retry; at the limit `FAILED` with category `RETRIES_EXHAUSTED` |
| any other 4xx | permanent | `FAILED` at once, category `PERMANENT_REJECTION`; never retried |

The stored and published failure reason is structured: `{category, code, httpStatus, attempt}` with codes from a fixed set (`PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`, `PROVIDER_REJECTED`, `PROVIDER_ERROR`). Provider response bodies are never stored.
