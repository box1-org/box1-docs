# Service 01 — Order service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


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

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** the order service and its required test doubles, contracts, manifests and documentation. Inventory, fulfillment, BFF, virtualization, mesh and AI operations are out of scope; use deterministic fixtures from `box1-ops-contracts` for their events.

**Discovery must cover:**

- whether `box1-ops-order` exists, and how `orders-service` and `quarkus-reference` differ from what this service needs;
- `box1-ops-contracts` as the shared source: `openapi/order-service.yaml`, `events/v1/`, `fixtures/events.json`, `TOPICS.md`, `postgres/OWNERSHIP.md`, `postgres/migrations/orders/`;
- each difference between those contracts and this prompt, resolved in design. Non-breaking additions go to `box1-ops-contracts` by PR; breaking changes are a stop condition;
- what the deployed Kafka and PostgreSQL provide today, including topics and any dead-letter path, and the open live-acceptance work in [box1-docs#31](https://github.com/box1-org/box1-docs/issues/31).

**Design decisions to record before implementation:**

- idempotency scope, payload fingerprinting and record retention;
- isolation or locking strategy for concurrent creates;
- legal transitions from each state, and handling of events after a terminal state;
- the explicit `COMPLETED` policy and the conditions for `EXCEPTION` and `CANCELLED`;
- retry bounds, poison-event routing and replay;
- migration ownership and compatibility;
- external, internal and administrative endpoints, with their authentication and authorization assumptions;
- customer fields allowed in logs and events;
- behavior when Kafka is unavailable.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | OpenAPI, event schemas and transition table cover this prompt; examples validate |
| 3 Implementation | Migrations apply cleanly; state history is immutable and attributable; timeline ordering is stable |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 6 GitOps delivery | Promotion PR is for this service only; `orders-service` is unchanged |
| 7 Live acceptance | One order lifecycle is followed through logs, metrics, traces and timeline, as far as deployed dependencies allow |

**Verification scenarios (local, using Testcontainers or Dev Services):** ten identical POSTs; same key with a changed body; concurrent duplicate creates; rollback during create; Kafka unavailable after commit; publisher restart while claiming; duplicate, out-of-order and post-terminal events; malformed envelopes; retry exhaustion to the dead-letter path; duplicate fulfillment requests; migration rerun; restart during message processing; database unavailable at readiness; unauthorized access to internal endpoints; customer data in logs or events.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
