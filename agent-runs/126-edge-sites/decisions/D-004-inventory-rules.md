# D-004 Pick, count and hold semantics in inventory-service

**Pick.** Records that the reserved units were picked; never changes `on_hand` or `reserved` (the shipment already
does). Matching ACTIVE/COMMITTED → picked; matching CONSUMED → picked after shipment; EXPIRED/RELEASED →
`PICK_NOT_HELD`; unknown or mismatch → `PICK_MISMATCH`. *Not taken:* decrementing `on_hand` at pick time (double
removal with the shipment).

**Count.** Latest count wins (by `countedAt`, tie by `countId`). `E = C + movements after countedAt` (shipments by
`shippedAt`); `on_hand := max(E, reserved, 0)` as a `COUNT` movement; `E < reserved` → `COUNT_CONFLICT`; no stock row →
`COUNT_UNKNOWN_STOCK`. Arrival-order independent. Known limit: a shipment confirmed after a count was applied but
shipped before it is subtracted again until the next count (inventory-service#7 architecture doc).

**Hold.** Recorded centrally for audit, no stock effect in v1; `RELEASED` without `PLACED` → `HOLD_UNKNOWN`.
*Not taken:* reducing available stock (interacts with reservations; future change).

**Pick list removal.** Expiry and confirmed shipment close items; a closure that arrives first is remembered. An
operator release publishes no event in v1, so released items stay listed until they expire or ship.
