# Service 01 — Order service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-01, FR-03, FR-04; DAT-03/04; OBS-01/02/03

**Dependencies:** Kafka, PostgreSQL, versioned event contracts. Initial implementation can validate HTTP and DB without a running broker.

## Mission and boundary

Own order commands, authoritative state, transitions, idempotency keys, the order event outbox and a customer-visible timeline. **Do not duplicate the completed `orders-service` Golden Path demonstration.** Proposed new repo: `box1-org/box1-ops-order`.

An order is a business aggregate, not a distributed transaction. Service may orchestrate the order saga by reacting to inventory and fulfillment events but must never read other services’ tables.

## Interfaces, domain behavior and implementation constraints

- `POST /api/v1/orders`: header `Idempotency-Key`, body `{customerId, sku, quantity (>0), siteId}`; atomic `order` row + idempotency record keyed by consumer/account scope and key + `order.placed.v1` outbox. `201` and Location for first request; same payload returns same order; same key with different payload `409`.
- `GET /api/v1/orders`, `GET /api/v1/orders/{orderId}`, `/timeline` with stable pagination, timestamps, current state, status reason, trace/correlation references; proper `404` and Problem JSON. Sensitive customer details must not go to logs/events.
- PostgreSQL migration tables: `orders`, `order_state_history`, `idempotency_records`, `outbox`, `processed_event`. Include unique constraints and lifecycle indexes.
- State transition guard: `SUBMITTED` → `RESERVED` → `FULFILLMENT_REQUESTED` → `SHIPPED` → `COMPLETED`; alternate `REJECTED`, `EXCEPTION`, `CANCELLED` under documented conditions. `FULFILLMENT_REQUESTED` may be displayed as “Awaiting ERP acknowledgement.”
- On `inventory.reserved.v1`: once per event/order, link `reservationId`, state transition to `RESERVED`, then enqueue `fulfillment.requested.v1` in same transaction. On `inventory.rejected.v1`: transition to `REJECTED`; on `shipment.confirmed.v1`: transition to `SHIPPED`, then `COMPLETED` only when an explicit completion policy applies. Unexpected late/duplicate events must not regress state.
- Outbox publisher is restart-safe, uses bounded batch/lease or safe claiming, retries with backoff, marks published only after broker confirmation; event key is `orderId`; metric `box1_outbox_pending` and oldest pending age. Keep transport and business write transactions distinct, explain at-least-once semantics.
- Propagate valid W3C `traceparent`, `correlationId`, `causationId`; JSON logs carry `orderId` and event ID but no sensitive customer data. Business meters: order age, lifecycle rates, stuck order count, outbox lag.

## Acceptance evidence (automate where practical)

- Same idempotency key + same body 10x returns one order and one initial outbox event; same key + changed body returns `409`.
- Concurrent duplicate POSTs (including at transaction boundary) return one persisted aggregate.
- Simulated Kafka failure after order commit leaves an unpublished outbox record; recovery emits it once logically and consumers remain idempotent.
- Event redelivery/out-of-order sequence doesn't duplicate fulfillment request or regress status; timeline remains ordered and attributable.
- Successful OpenAPI examples, DB migrations, readiness failing if DB unavailable, and metrics can be inspected locally.

## Recommended 64K-safe implementation slices

1. Scaffold or inspect independent Golden Path service and implement create/read endpoints + migration.
2. Add state machine and timeline API, concurrency tests and Problem JSON.
3. Add event envelopes and transactional outbox + broker-down recovery tests.
4. Consume inventory/fulfillment events idempotently; add saga transition tests.
5. Add cross-service traces, business metrics, dashboards/runbook references and GitOps proof.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
