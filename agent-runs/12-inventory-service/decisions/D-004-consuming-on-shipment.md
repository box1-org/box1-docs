# D-004 Consuming stock on shipment

**Status:** decided by the agent in Phase 1, 2026-11-05. Needs an additive `TOPICS.md` row and a state addition in contracts.

Inventory joins `box1.fulfillment.events.v1` as group `inventory`.

| Hold | `shipment.confirmed.v1` for its `orderId` | Effect |
|---|---|---|
| `ACTIVE` or `COMMITTED` | first | `CONSUMED`; `on_hand` and `reserved` both fall by quantity, in one transaction |
| `CONSUMED`, same `shipmentId` | any | no effect |
| `CONSUMED`, different `shipmentId` | any | no stock effect; reconciliation item `SHIPMENT_DUPLICATE` |
| `COMMITTED`, other `fulfillmentRequestId` | any | no effect; item `SHIPMENT_REQUEST_MISMATCH` |
| `EXPIRED` or `RELEASED`, first | late | item `SHIPMENT_AFTER_RELEASE`. `on_hand` falls only if `on_hand - reserved >= quantity`; the item records whether it did. The hold's state does not change. |
| `EXPIRED` or `RELEASED`, same `shipmentId` | any | no effect |
| `EXPIRED` or `RELEASED`, different `shipmentId` after an adjustment | any | item `SHIPMENT_DUPLICATE`; no second deduction |
| none | any | reconciliation item `SHIPMENT_WITHOUT_RESERVATION` |

`ACTIVE` is accepted because the two topics have no mutual ordering, so a shipment can overtake the `fulfillment.requested.v1` signal.

`reconciliation_item` is durable and counted by `box1_inventory_reconciliation_open`. No tooling resolves these items in v1, the same limit Order has for `EXCEPTION`. Stock is never released as a result of a confirmed shipment.
