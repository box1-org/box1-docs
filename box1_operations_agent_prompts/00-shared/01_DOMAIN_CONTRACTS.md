# Canonical domain and integration contracts — v1 proposed baseline

These contracts are the cross-service coordination baseline. They are **not existing deployed facts**. Create actual JSON Schemas and OpenAPI specs as the first platform slice, then treat versioned contract files as source of truth. Do not let each agent invent incompatible event names or fields.

## Ownership and order lifecycle

| Owner | Owns | Never owns |
|---|---|---|
| Order | Order state, command idempotency, order timeline, outbox | Inventory balances, ERP internals |
| Inventory | Site stock, available-to-promise, reservations, expiry | Order state transitions |
| Fulfillment adapter | ERP requests, retries, dedupe, receipts, reconciliation | Order primary state, ERP ledger |
| ERP VM simulator | Simulated legacy shipment ledger, acknowledgement and faults | Order-service tables |
| Telemetry | Sensor readings, threshold alerts, ingestion control | Order fulfillment decisions |
| Notification | Delivery attempts and templates | Order source of truth |
| AI Operations | Evidence retrieval, citations, read-only tools, approval proposal records | Direct, automatic cluster mutations |
| Experience/BFF | UI aggregation, role-based view models, query composition | Authoritative business writes |

Order path: `SUBMITTED` → `RESERVED` → `FULFILLMENT_REQUESTED` → `SHIPPED` → `COMPLETED`. Alternate states: `REJECTED` (inventory unavailable), `EXCEPTION` (manual reconciliation required), `CANCELLED` (only when safe). Display `FULFILLMENT_REQUESTED` as **Awaiting ERP acknowledgement** in UI. State transitions must be guarded and recorded with reason and event linkage.

## Core HTTP endpoints (proposed)

- **Order** `POST /api/v1/orders` body `{customerId, sku, quantity, siteId}` with mandatory `Idempotency-Key` header, returns `201` + Location for new resource; repeated same key and payload returns same order, key+different payload returns `409`. `GET /api/v1/orders`, `GET /api/v1/orders/{orderId}`, `GET /api/v1/orders/{orderId}/timeline`, `GET /api/v1/orders/{orderId}/exceptions` if implemented.
- **Inventory** `GET /api/v1/inventory?siteId=&sku=`, `GET /api/v1/reservations/{reservationId}`; writes originate from versioned commands/events; no unrestricted stock mutation from public UI.
- **Fulfillment adapter** `GET /api/v1/fulfillments/{orderId}`, `POST /internal/v1/fulfillments/{orderId}/reconcile` protected and auditable; may omit write operation from externally routed API.
- **ERP simulator** `POST /api/v1/erp/shipments` with `Idempotency-Key` or `fulfillmentRequestId`, `GET /api/v1/erp/shipments/{id}` and `GET /health`; support deterministic demo faults behind secured controls.
- **Telemetry** `POST /api/v1/telemetry/readings` (internal/authenticated), `GET /api/v1/assets/{assetId}/readings`, `GET /api/v1/alerts`.
- **Notification** `GET /api/v1/notifications?orderId=`, optional internal test-only delivery provider.
- **AI Operations** `POST /api/v1/ai/incidents/{incidentId}/analyze`, `GET /api/v1/ai/analyses/{analysisId}`, `GET /api/v1/ai/tools`, `POST /api/v1/ai/actions/{actionId}/propose` (not execute without separate human approval).
- **BFF** `GET /api/v1/overview`, `GET /api/v1/orders/{id}/summary`, `GET /api/v1/incidents/{id}/evidence`.

Use RFC 9457 `application/problem+json` errors (or document an explicitly consistent exception). Pagination, request validation and OpenAPI required. AuthN/AuthZ apply at the BFF **and** backend boundaries; never trust only frontend hiding.

## Event envelope — v1

```json
{
  "eventId": "uuid",
  "eventType": "order.placed.v1",
  "schemaVersion": 1,
  "aggregateId": "ord_1042",
  "occurredAt": "2026-10-25T12:30:00Z",
  "correlationId": "uuid-or-opaque-trace-link",
  "causationId": "previous-eventId-or-commandId",
  "traceparent": "00-<trace-id>-<span-id>-01",
  "payload": { "orderId": "ord_1042" }
}
```

Define `tracestate` optionally and use valid W3C identifiers in real data. Keep envelope metadata stable across versioned domain schemas. Partition order-lifecycle events by `orderId` to preserve per-order ordering. All producers document keying and retention. Accept `at least once` delivery and implement deduplication transactionally.

| Kafka topic proposal | Event types and producer | Typical consumer |
|---|---|---|
| `box1.order.events.v1` | `order.placed.v1`, `fulfillment.requested.v1`, `order.state-changed.v1` — Order | Inventory, fulfillment, BFF projections |
| `box1.inventory.events.v1` | `inventory.reserved.v1`, `inventory.rejected.v1`, `inventory.reservation-expired.v1` — Inventory | Order |
| `box1.fulfillment.events.v1` | `shipment.confirmed.v1`, `shipment.failed.v1` — Fulfillment adapter | Order, notifications |
| `box1.telemetry.events.v1` | `equipment.reading.v1`, `equipment.threshold-exceeded.v1` — Telemetry | Telemetry projection/incident views |
| `box1.notification.events.v1` | `notification.requested.v1`, `notification.delivered.v1`, `notification.failed.v1` — Order/Notification | Notification/history |

Contract payload minima:

- `order.placed.v1`: `orderId, customerId, sku, quantity, siteId`.
- `inventory.reserved.v1`: `orderId, reservationId, sku, quantity, siteId, expiresAt`.
- `inventory.rejected.v1`: `orderId, sku, quantity, siteId, reasonCode`.
- `fulfillment.requested.v1`: `orderId, reservationId, fulfillmentRequestId, siteId, sku, quantity`.
- `shipment.confirmed.v1`: `orderId, fulfillmentRequestId, shipmentId, shippedAt`.
- `shipment.failed.v1`: `orderId, fulfillmentRequestId, retryable, reasonCode`.
- `equipment.reading.v1`: `assetId, siteId, measuredAt, metricName, value, unit`.
- `equipment.threshold-exceeded.v1`: `assetId, siteId, metricName, value, threshold, severity`.

## Recovery invariants

1. Every accepted order has an immutable `orderId`. A repeated create command cannot allocate stock twice.
2. Reservation transactions are atomic and non-negative; reservations have explicit TTL and lifecycle.
3. The order service writes state change and outbox row in one DB transaction; an outbox publisher may replay safely.
4. Every event consumer records `eventId` within the same DB transaction as its effects. Duplicate events are acknowledged without repeating business effects.
5. ERP adapter deduplicates by `fulfillmentRequestId`; ERP simulator must also honor that identifier.
6. Poison events go to a bounded retry/DLQ path with metrics and protected, auditable replay; never silently discard.
7. Events contain no secrets or customer-sensitive payloads beyond minimally necessary opaque IDs.
8. Never implement a distributed cross-service transaction or promise transport-level exactly-once delivery.

## Versioning governance

Commit OpenAPI and JSON Schema files together with compatibility tests. Additive v1 changes may be backwards compatible; breaking changes require `v2` events/endpoints, dual-read/dual-write migration strategy and consumers' approval. The shared contracts repository is proposed as `box1-org/box1-ops-contracts`.
