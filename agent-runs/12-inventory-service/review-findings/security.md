# Security pass

Reviewed `9d6deed` by reading code and library bytecode. No high or medium findings.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| 1 | Low | A top-level `groups` claim could grant the admin role. | **Fixed.** The role must be in the client's own claim. Test added. |
| 2 | Low | Reported to the user directly, per this run's public-repository rule. | **Open for the user.** Requires a shared smoke task change. |
| 3 | Low | `correlationId` had no character rule. | **Fixed.** |
| 4 | Low | Dead-letter retention is double the source's, and carries customer IDs. | **Documented** in the runbook. Retention matches `box1.order.dlq.v1`. |

Test gap closed: invalid tokens on read routes. A mistyped policy is covered by the exact-match code, with no dedicated test.

Also confirmed: route guard independent of path form, JWT verification, audit actor, metric tag bounds, log and header content, customer ID handling, CORS and request limits. The reviewer did not open the Secret manifest.
