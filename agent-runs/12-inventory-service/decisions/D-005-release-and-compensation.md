# D-005 Release and compensation

**Status:** decided by the agent in Phase 1, 2026-11-05.

What can happen today, from `order-service` main and order run D-009 and D-010:

- `REJECTED` orders hold nothing, because Inventory's own rejection caused them.
- `CANCELLED` is legal only from `SUBMITTED`, and no endpoint performs it. A cancel can still race an outgoing reservation.
- `EXCEPTION` means manual reconciliation.

**Behavior:**

- `order.state-changed.v1` with `toState = CANCELLED`: an `ACTIVE` hold becomes `RELEASED`. Otherwise no effect, or an item if it is `COMMITTED`. Tested with fixtures, since nothing produces it live.
- `order.state-changed.v1` with `toState = REJECTED` or `EXCEPTION`: no automatic effect. An `ACTIVE` hold expires on its TTL.
- `shipment.failed.v1` with `retryable = false`: the hold stays, and item `SHIPMENT_FAILED` is opened. Goods may have moved, so a person decides.
- `shipment.failed.v1` with `retryable = true`: no effect.
- **Operator release:** `POST /internal/v1/reservations/{id}/release`, authenticated (D-010). Only `ACTIVE` or `COMMITTED`. A repeat returns the same result with no second effect. `CONSUMED` and `EXPIRED` return 409. Audited in `reservation_history` and `stock_movement`, with the subject and a required reason.

No new event is published on release. The contracts have no such event and Order has no consumer for one.

**Today, in practice:** nothing triggers an automatic release live. Until the Keycloak client exists (D-010) a stuck `COMMITTED` hold can only be released by a forward data migration through a PR.
