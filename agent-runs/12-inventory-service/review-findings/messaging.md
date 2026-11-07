# Messaging pass

Reviewed `9d6deed` by reading code and connector bytecode. No high findings. No lost-event or double-effect path.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| M1 | Medium | A database outage over about 7 minutes dead-letters valid events, with harm that depends on type. | **Fixed.** Availability errors hold position, using no attempts. D-007 amended. Test uses an injected `57P03`. |
| M2 | Medium | After an outage, expiry beats a signal already on the topic. Same as Architecture M1, found independently. | **Fixed**, with the same limit. |
| M3 | Medium | A failed dead-letter send stops the channel and crash-loops until the topic works. No record lost. | **Mitigated by order.** Topic merge is step 2 of First deployment. Failure path **not tested**. |
| L1 | Low | Permanent database errors got the full retry. | **Fixed.** |
| L2 | Low | Parser looser than contract: coerced `schemaVersion`, invalid UTF-8, loose UUIDs. | **Fixed.** Tests added. |
| L3 | Low | Floor edges: runbook said `order.placed.v1` only, and a future floor silently skips orders. | **Fixed.** Runbook corrected, and a future floor refuses to start. Malformed pre-floor records still dead-letter, by design. |
| L4 | Low | Expiry `causationId` names the placing event, while the fixture uses the reserved event. | **Accepted and documented.** The schema does not constrain it, and Order does not use it. |

Not established: behavior of an interrupted retry at shutdown. Not run against a real broker by the reviewer; the suite covers the DLQ path.
