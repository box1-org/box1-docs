# Service 02 — Inventory service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-02, DAT-01/02/04/05

**Dependencies:** `order.placed.v1`, Kafka + PostgreSQL, shared schema contracts.

## Mission and boundary

Own per-site SKU inventory, available-to-promise, reservations, expiry and denial reasons. Proposed new repo `box1-org/box1-ops-inventory`. The inventory boundary never directly updates order records.

## Interfaces, domain behavior and implementation constraints

- DB model: `inventory_stock(siteId,sku,onHand)`, `reservations(reservationId,orderId,sku,siteId,quantity,status,expiresAt)`, `processed_event`, `outbox`. Available quantity equals on-hand minus active reservations; ensure no negative available balance.
- Consume `order.placed.v1` keyed by `orderId`. Execute conditional locked/optimistically versioned stock reservation atomically with processed-event dedupe and outbox. Publish exactly one business outcome: `inventory.reserved.v1` with `reservationId`/`expiresAt`, or `inventory.rejected.v1` with stable reason codes `UNKNOWN_SKU`, `INSUFFICIENT_STOCK`, `SITE_UNAVAILABLE` etc.
- Explicit TTL expiry and deterministic scheduler that is idempotent. Expiration emits `inventory.reservation-expired.v1`; provide compensation/release procedure for terminal rejected/cancelled orders. Avoid releasing stock once shipment confirmed without a defined reconciliation path.
- Read API `GET /api/v1/inventory?siteId=&sku=` and `GET /api/v1/reservations/{id}`. Write/admin restocking is internal, authenticated and auditable; consider test fixture insert via Flyway and admin-only fixture command.
- Handle Kafka redelivery, consumer restarts, poison payload, schema mismatch, bounded retries and DLQ/inspection. Producer uses shared envelope and partition key `orderId`.
- Metrics: reserved units by site, denials by reason, reservation conflict retries, event age, expired count and DLQ length; logs/traces are correlated to order ID.

## Acceptance evidence (automate where practical)

- Two simultaneous orders for final item yield exactly one reservation, one rejection, no negative inventory.
- Reprocessing any `eventId` or equivalent order command yields no additional hold and no duplicate outcome.
- Stock and reservation record + outbound event are atomic; broker outage cannot lose the result.
- Reservation expiry is reproducible with a clock-driven test; restore seeded inventory fixture afterward.
- Query API reflects site-specific available-to-promise values and exposes no unauthorized mutation route.

## Recommended 64K-safe implementation slices

1. Schema/stock query and concurrency-safe transaction + tests.
2. Kafka consumer and result outbox/idempotency records.
3. Expiry, compensation and denial semantics with deterministic fake clock.
4. Metrics, traced events, poison message handling and user-facing documentation.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
