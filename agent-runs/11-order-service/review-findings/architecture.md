# Architecture pass

Reviewed commit 764ada1 in a fresh subagent, by reading only. These same-model passes do not replace human PR review or CI. Fixes landed in 078f341, retested with the full container suite.

| Severity | Finding | Outcome |
|---|---|---|
| Medium | A database outage over 7.5 s dead-lettered valid events; a later replay could apply a reservation after its expiry | **Fixed.** Consumers hold position for about 7 minutes. A reservation past `expiresAt` moves to `EXCEPTION`. The ordering limit past the budget is documented. |
| Medium | Reservation content was not compared with the order; required payload fields went unvalidated | **Fixed.** Mismatch moves to `EXCEPTION`. The parser checks every required field. |
| Low | Decision D-011 drifted from the code | **Fixed.** D-011 updated. |

No defects in state ownership, cross-service reads, explicit transitions or distributed transactions.
