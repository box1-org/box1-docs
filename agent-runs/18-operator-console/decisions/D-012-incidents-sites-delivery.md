# D-012 Incidents, sites and delivery pages without a contract

**Status:** decided.

- **No incident contract exists** (gap noted in the mockup, decision 2).
  - The console **derives** incidents from upstream observations: an order in `EXCEPTION`, an order `FULFILLMENT_REQUESTED` for more than 10 min (configurable), or an adapter `NEEDS_ATTENTION`/`REJECTED`.
  - Incident id is `inc_<orderId>`. Evidence is that order's timeline, reservation, fulfillment and revisions.
  - The page says "derived by the console", and #17 replaces the derivation with the real contract.
- **Telemetry alerts would join incidents**, but asset-service refuses console tokens (G-2). Its source reads `NOT_AUTHORIZED` with that reason.
- **Sites:** stock by site from inventory (`GET /api/v1/inventory`). The asset alerts panel shows `NOT_AUTHORIZED` (G-2).
- **Delivery panel (P1)** is in scope because it is cheap: each upstream's `/api/info` gitRef and the console's own, needing `console-developer`.

## Amendment (Phase 5, ARCH-2/ARCH-6)

- Incidents are derived from **order status only**. Adapter-derived incidents are not implemented.
- For an order with no incident condition, the evidence endpoint returns `kind: NONE` and "No active incident". It claims no past incident and no resolution.
