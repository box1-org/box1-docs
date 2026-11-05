# Persistence pass

Reviewed commit 764ada1 in a fresh subagent, by reading only. These same-model passes do not replace human PR review or CI. Fixes landed in 078f341, retested with the full container suite.

No high or medium findings.

| Severity | Finding | Outcome |
|---|---|---|
| Low | Publisher fail-fast did not fire on metadata timeouts | **Fixed.** See the messaging pass. |
| Low | Event time read before the row lock, so times could invert against sequence | **Fixed.** Read after the lock. |
| Low | First response carried nanoseconds, later reads microseconds | **Fixed** and tested. |
| Low | NUL in `sku` returned 503 | **Fixed.** Control characters return 400. |
| Low | Index could not serve the claim's order; `ix_orders_state` unused | **Fixed** in V1, which has not been applied anywhere. Plans were not measured with EXPLAIN. |
| Low | Published outbox rows are never purged | **Open, next action:** add a retention job when growth is measured. |

No defects in JTA enlistment, READ COMMITTED races, the deferred foreign key, SKIP LOCKED ordering, or lease handling. The reviewer's JTA conclusion rests on framework knowledge; the concurrency scenarios pass in the local suite.
