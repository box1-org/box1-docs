# Persistence pass

Reviewed `9d6deed` by reading code and reasoning about READ COMMITTED. No high findings.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| 1 | Medium | Late shipment reduces `on_hand` more than once. Same as Architecture M2, found independently. | **Fixed.** |
| 2 | Low | `reservation_history.from_status` could be stale. Same as Architecture L3. | **Fixed.** |
| 3 | Low | Permanent data errors retried as if transient, for example a NUL in `correlationId`. | **Fixed.** Control characters are rejected, and SQLState 22 and 23 go straight to poison, except 23505. |
| 4 | Low | The drift gauge has no index. Audit, outbox and dedupe tables are never pruned. | **Index added.** Pruning: **recorded, not done**, no volume yet. Same open item as the order run. |

Also confirmed: transaction boundaries, the last-unit race, the same order concurrently, single winner on one hold, drift unreachable, outbox indexes, migrations. Recorded limitation: one login both migrates and runs (D-012, box1-docs#41).
