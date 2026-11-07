# D-014 Modern status model

**Status:** decided by the agent in Phase 1, 2026-11-05.

`GET /api/fulfillments/{id}` reports four separate facets:

| Facet | Values |
|---|---|
| `acceptance` | `ACCEPTED` (always, once the row exists) |
| `dispatch` | `QUEUED`, `UPLOADED`, `NEEDS_ATTENTION` |
| `erpAcknowledgement` | `NONE`, `ACKNOWLEDGED` (any applied `RES`) |
| `outcome` | `AWAITING_ERP`, `PENDING` (ERP waiting), `HELD` (operator hold; not a failure), `SHIPPED`, `REJECTED` |

Plus `revision`, `shipmentId`, `reasonCode` (never `reasonText`), `needsAttentionReason`, attempt counts and timestamps. `SHIPPED` → `shipment.confirmed.v1`; `REJECTED` → `shipment.failed.v1 retryable:false`. `PENDING` and `HELD` produce no event.
