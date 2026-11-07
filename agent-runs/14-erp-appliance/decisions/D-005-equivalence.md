# D-005 Request identity and equivalence

**Identity:** `fulfillmentRequestId`.

**Same content** means equal `orderId`, `reservationId`, `siteId` and the same ordered list of (`lineNo`, `sku`, `quantity`). Excluded: file name, header timestamp, `origin`, `requestedAt`, `correlationId`. REST and Kafka submissions of the same request therefore compare equal, as #13 needs.

**Repeat with same content:** no new revision; the ERP re-publishes the latest existing result unchanged (same result ID and bytes).

**Repeat with different content:** the file is quarantined with error code `CONFLICTING_REUSE`, an `ERR` file is published, and the existing request is untouched.
