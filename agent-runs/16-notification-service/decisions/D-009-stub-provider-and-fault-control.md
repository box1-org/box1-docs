# D-009 Stub provider and fault control

**Status:** design decided by the run. **The demo namespace must be named by the user. Any stub fault run on the cluster needs approval.**

## Stub provider

- `stub` is the only provider. Real providers are an interface with no implementation; selecting one fails startup.
- In-process. On success it writes one receipt per `notificationId`: `receiptId = "rcpt_" + first 24 hex of SHA-256(notificationId + templateVersion + bodySha256)`, `channel`, `bodySha256`, `bodyLength`, `acceptedAt`. The body itself is not in the receipt (redacted). The same `notificationId` returns the existing receipt.

## Fault modes

| Mode | Effect | Class (D-004) |
|---|---|---|
| `TRANSIENT_503` | returns 503 | transient |
| `SLOW` | waits `delayMillis` (100–5000, default 3000) before succeeding; the worker's 2 s timeout makes it a timeout above 2 s | transient if over the timeout |
| `PERMANENT_4XX` | returns 422 | permanent |

Optional `failCount` (1–20): after that many faulted calls the stub behaves normally again, which demonstrates "503, retries, then success" without waiting for the TTL.

## Control and bounds (enforced server-side)

- `POST /api/v1/stub/faults {mode, ttlSeconds, delayMillis?, failCount?}`, `DELETE /api/v1/stub/faults`; role `notification-fault-operator`.
- One active fault at a time; a new one replaces the old one (audited).
- `ttlSeconds` 10–900; hard cap compiled in (15 min); config can only lower it. Expiry is checked against database time on every provider call, and a scheduled sweep records `EXPIRED` in the audit.
- Gate: `NOTIFY_STUB_FAULTS_ENABLED=true` **and** the pod namespace (downward API `POD_NAMESPACE`, not service-controlled config) is in `NOTIFY_STUB_FAULT_NAMESPACES`. Otherwise `403` Problem JSON with code `FAULTS_DISABLED`, `NAMESPACE_UNKNOWN` or `NAMESPACE_NOT_ALLOWLISTED`. The image and the deployment ship with faults disabled and an empty allowlist.
- Audit: append-only `stub_fault_audit (id, at, actor, action, mode, ttl_seconds, outcome, namespace)`; a trigger rejects UPDATE/DELETE within 90 days and TRUNCATE always. Actor is `preferred_username`, else `sub`. Refusals are audited too.
- The stub faults affect only this service's own deliveries.

No configuration-only switch for a fault: configuration enables the gate, the endpoint switches the mode, so every fault has an actor and a TTL.
