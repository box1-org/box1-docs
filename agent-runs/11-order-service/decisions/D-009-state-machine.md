# D-009 Legal transitions and post-terminal events

**Status:** decided by the agent in Phase 1, 2026-11-05.

The contract copy lives in `box1-ops-contracts` `ORDER-STATE.md`.

| From | Event | Result |
|---|---|---|
| SUBMITTED | `inventory.reserved.v1` | RESERVED, then FULFILLMENT_REQUESTED; enqueue `fulfillment.requested.v1` in the same transaction |
| SUBMITTED | `inventory.rejected.v1` | REJECTED |
| SUBMITTED | `shipment.confirmed.v1` | EXCEPTION: `SHIPMENT_BEFORE_RESERVATION` |
| FULFILLMENT_REQUESTED | `shipment.confirmed.v1` | SHIPPED, then COMPLETED if policy allows |
| FULFILLMENT_REQUESTED | `shipment.failed.v1`, `retryable=false` | EXCEPTION: `SHIPMENT_FAILED` |
| FULFILLMENT_REQUESTED | `shipment.failed.v1`, `retryable=true` | no state change; timeline note |
| FULFILLMENT_REQUESTED | `inventory.reservation-expired.v1` | EXCEPTION: `RESERVATION_EXPIRED` |
| Any other pair | any | no state change; timeline note `IGNORED_<state>`; counted in a metric |

- REJECTED, COMPLETED, CANCELLED and EXCEPTION accept no event-driven transition. Late events only add a note.
- An exact redelivery (same `eventId`) adds nothing, not even a note.
- Unknown `orderId`: treated as poison, see D-011. Events for an order this service never created cannot be applied.
