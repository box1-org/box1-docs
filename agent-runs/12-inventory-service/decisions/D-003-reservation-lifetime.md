# D-003 Reservation lifetime against a healthy order

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Both a TTL and a signal.**

- A new hold is `ACTIVE` with `expiresAt = now + INVENTORY_RESERVATION_TTL`, default `PT15M`. The TTL covers the gap until Order acts, and protects stock if an order is abandoned or Order is down.
- `fulfillment.requested.v1` on `box1.order.events.v1`, whose `reservationId` and `orderId` match, moves `ACTIVE` to `COMMITTED`. **A `COMMITTED` hold does not expire.** That is what stops a slow but healthy order going to `EXCEPTION`, however long the ERP takes.
- The topic already lists `inventory` as a consumer, so this needs no contract change. `order.state-changed.v1` is not used as the signal, since `fulfillment.requested.v1` carries the IDs.
- `COMMITTED` age is measured by `box1_inventory_committed_oldest_age_seconds`, so a stuck hold is visible instead of silently holding stock.

**Races:** expiry and commit are each one conditional `UPDATE ... WHERE status = 'ACTIVE'`, so exactly one wins. If expiry wins, the late signal changes nothing and files a reconciliation item. Order then receives the expiry after its own request, and goes to `EXCEPTION`, its documented rule.

**Order down past the TTL:** Inventory expires the hold. Order later sees `inventory.reserved.v1` past `expiresAt`, and goes to `EXCEPTION` with `RESERVATION_EXPIRED`. No double allocation.

**Today, with no fulfillment adapter deployed:** a reserved live order rests at `FULFILLMENT_REQUESTED`, its hold `COMMITTED`, indefinitely. That is the correct state, and the live test order will tie up its units until released (D-005).
