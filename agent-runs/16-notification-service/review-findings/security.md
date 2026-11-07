# Security pass

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`).

Scope covered as the profile requires: the API, the fault control and the logs. No high or medium findings.

No-finding items: issuer/signature/expiry/audience; azp-scoped roles, groups ignored, other-client tokens refused, console tokens never get fault control; deny-by-default; Problem JSON leaks nothing; fault bounds server-side with DB-time TTL and downward-API allowlist; logs carry no tokens, payloads or customer data; DLQ headers fixed text; `order.placed` customer field never read; templates allowlisted and escaped; no secrets in source, tests or manifests; DB credential by `secretKeyRef`; NetworkPolicy; TLS Route; 4 KiB body limit; parameterized SQL.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| L1 | Low | Refusals before the handler (401/403) and body-read rejections are not audited | **Fixed** for 401/403 on fault paths (`DENIED_*` rows with actor); body-read rejections **recorded** in the runbook as not audited |
| L2 | Low | Keycloak ID tokens pass verification | **Fixed.** `typ` must be `Bearer`; test with an ID token gets 401 |
| L3 | Low | Actor is a mutable username | **Fixed.** `actor_subject` (`sub`) stored too |
| L4 | Low | App role owns the audit table and could drop its trigger | **Recorded** as a lab limitation pending a separate migration owner (#41) |
| I1 | Info | DLQ keeps `customerId` of a poisoned `order.placed.v1` | **Open decision** O-7 |
| I3 | Info | CORS allowed unused PUT/PATCH | **Fixed** |
| I6 | Info | Truncation could split a surrogate pair | **Fixed**; test added |
| I2, I4, I5, I7 | Info | Anonymous `/q/*`; renewable TTL; plaintext Kafka; Keycloak role creation | **Recorded**; I5 is platform scope, I7 is a post-sync check in the runbook |
