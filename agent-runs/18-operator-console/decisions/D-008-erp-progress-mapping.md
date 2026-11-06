# D-008 ERP progress mapping and the order → fulfillment link

**Status:** the mapping is decided. **The link needs the user's decision (O-1, gap G-1).**

## Mapping (applied only when the order is `FULFILLMENT_REQUESTED`, `SHIPPED` or `COMPLETED`)

| Adapter observation | Label | Tone |
|---|---|---|
| adapter unreachable, timeout or 5xx | order-service label plus **"ERP detail unavailable"** | unknown |
| link not available (G-1 not resolved) | order-service label plus **"ERP detail unavailable"**, detail "no published order→fulfillment link" | unknown |
| 404 for the fulfillment id | **"Not yet received by the fulfillment adapter"** | waiting |
| `dispatch=NEEDS_ATTENTION` (any outcome except SHIPPED/REJECTED) | **"Needs attention"** plus `needsAttentionReason` | attention |
| `outcome=REJECTED` | **"Rejected by the ERP"** | failure |
| `outcome=SHIPPED` | **"Shipped"** plus `shipmentId` | done |
| `outcome=HELD` | **"Held by an ERP operator"**, with the note "waiting, not a failure" | waiting |
| `outcome=PENDING` | **"Accepted by the ERP"** (awaiting processing) | waiting |
| `outcome=AWAITING_ERP`, `dispatch=UPLOADED` | **"Uploaded, awaiting ERP acknowledgement"** | waiting |
| `outcome=AWAITING_ERP`, `dispatch=QUEUED` | **"Queued for the ERP"** | waiting |

- **Precedence:** terminal outcomes first, then NEEDS_ATTENTION, then the rest.
- "Outstanding attempts" shows the adapter's `uploads` and `resends` counters and `statusAt`.
- The order-service state label is always shown alongside, so the two sources never merge into one guessed state.

## Order → fulfillment link (G-1)

- No published field links them. order-service computes `ful_<suffix of ord_>` internally (OrderService.java:88-89) but does not expose it, and the adapter has no lookup by orderId.
- **Implemented as a switch:** `CONSOLE_FULFILLMENT_LINK=derived|none`.
  - `derived` uses the convention, and the UI labels it "derived link".
  - `none` shows "ERP detail unavailable".
- **Default in Git is `none`** until the user decides (O-1). The permanent fix is to expose `fulfillmentRequestId` on the order API, a change to order-service and its contract, which is out of this run's scope.
