# D-004 Line items against the single-SKU fulfillment.requested.v1

**Decision:** the file protocol carries 1..99 `LIN` records per request. A `fulfillment.requested.v1` event maps to exactly one `LIN` with `lineNo` 1, `sku` and `quantity` copied unchanged. No field is dropped: every required v1 field has a place (`orderId`, `reservationId`, `fulfillmentRequestId`, `siteId` on `REQ`; `sku`, `quantity` on `LIN`).

**Why:** multi-line support costs nothing in the file format and avoids a future protocol v2, while v1 events stay unchanged. **No event contract change is required, so the breaking-change stop does not fire.** A future multi-line command would be a new event version, not a protocol change.
