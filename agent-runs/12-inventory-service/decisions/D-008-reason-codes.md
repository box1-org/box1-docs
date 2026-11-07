# D-008 Rejection reason codes

**Status:** decided by the agent in Phase 1, 2026-11-05.

The closed v1 set, so "etc." in the prompt means nothing further:

| Code | Meaning |
|---|---|
| `UNKNOWN_SKU` | The site is available and has no stock row for this SKU |
| `INSUFFICIENT_STOCK` | A stock row exists, and `on_hand - reserved` is below the quantity |
| `SITE_UNAVAILABLE` | The site is unknown, or marked unavailable. A separate unknown-site code is not added. |

Order keeps `reasonCode` as text matching `^[A-Z][A-Z0-9_]*$`, and any of these moves it to `REJECTED`. The schema stays a pattern. The set is documented in contracts, and adding a code is additive. Check order: site, then SKU, then quantity.
