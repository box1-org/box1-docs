# D-003 Request identity and REST body

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Gap:** what a REST caller sends when it has no `fulfillmentRequestId`.

**Decision:** the REST body is exactly the `fulfillment.requested.v1` payload: `fulfillmentRequestId`, `orderId`, `reservationId`, `siteId`, `sku`, `quantity`, all required, unknown fields rejected. The caller always supplies `fulfillmentRequestId`; the adapter never generates one, because a generated ID makes a client retry a new request. One line per request, as D-004 of #14 maps events.

**Consequences:** REST and Kafka submissions of the same request are equivalent by construction (ERP1 section 6). Multi-line REST requests are excluded until a modern contract carries lines.
