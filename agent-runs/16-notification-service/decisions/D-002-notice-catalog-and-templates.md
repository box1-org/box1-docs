# D-002 Notice catalog, channels and template versioning

**Status:** decided by the run (reversible: catalog and channel map are code + config).

Notices surface what an operator would otherwise miss or needs to act on. Recipients are named operator channels only.

| Trigger | Notice type | Channel | Fact key (D-003) |
|---|---|---|---|
| `order.state-changed.v1` `toState=SHIPPED` | `ORDER_SHIPPED` | `ops-fulfillment` | `ORDER_SHIPPED:{orderId}` |
| `shipment.confirmed.v1` | `ORDER_SHIPPED` | `ops-fulfillment` | `ORDER_SHIPPED:{orderId}` |
| `shipment.failed.v1` `retryable=true` | `SHIPMENT_DELAYED` | `ops-fulfillment` | `SHIPMENT_DELAYED:{orderId}:{fulfillmentRequestId}:{reasonCode}` |
| `shipment.failed.v1` `retryable=false` | `SHIPMENT_FAILED` | `ops-fulfillment` | `SHIPMENT_FAILED:{orderId}` |
| `order.state-changed.v1` `toState=EXCEPTION`, `reasonCode=SHIPMENT_FAILED` | `SHIPMENT_FAILED` | `ops-fulfillment` | `SHIPMENT_FAILED:{orderId}` |
| `order.state-changed.v1` `toState=EXCEPTION`, any other reason | `ORDER_EXCEPTION` | `ops-orders` | `ORDER_EXCEPTION:{orderId}` |
| `order.state-changed.v1` `toState=REJECTED` | `ORDER_REJECTED` | `ops-orders` | `ORDER_REJECTED:{orderId}` |

No notice (acknowledged, counted as `ignored`): `toState` `SUBMITTED`, `RESERVED`, `FULFILLMENT_REQUESTED`, `COMPLETED`, `CANCELLED`; `order.placed.v1` and `fulfillment.requested.v1`. **`COMPLETED` is deliberately excluded:** under the completion policy it follows `SHIPPED` immediately, so a second notice would be noise. Adding it later is a catalog entry, not a schema change.

`order.placed.v1` payloads are never parsed (it is the only event with `customerId`); only the envelope's `eventType` is read.

## Templates

- Each notice type has a template identified by `{noticeType}@v{n}`; v1 for all types now. The version is stored on the intent and in the outbound events. A changed wording is a new version; existing intents keep the version they were rendered with.
- Templates are plain text, rendered once when the intent is created, from an allowlist of fields: `orderId`, `fulfillmentRequestId`, `shipmentId`, `reasonCode`, `fromState`, `toState`, and timestamps. No other field reaches a template.
- Every substituted value is escaped: control characters (including CR/LF) are replaced, `<`, `>`, `&`, `"`, `'`, backtick and `|` are entity-encoded, and values are cut to 128 characters. Inputs are already constrained by contract patterns; escaping is defence in depth and is unit-tested with injection strings.
- When one fact arrives through two events, the notice is rendered from the first event that arrives; later sources are recorded against the same intent (D-003).
