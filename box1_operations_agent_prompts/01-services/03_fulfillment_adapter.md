# Service 03 — Fulfillment adapter


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-05, DAT-04/05, VM-02; P1 · VM-04

**Dependencies:** `fulfillment.requested.v1`, ERP simulator REST contract, Kafka/PostgreSQL.

## Mission and boundary

Protect the legacy ERP from unreliable upstream and unreliable transport. Proposed repo `box1-org/box1-ops-fulfillment`. This adapter owns request/acknowledgement state, deduplicated external effects, retry bounds and reconciliation. It must operate first against an HTTP simulator container, then an identical API hosted inside a VM.

## Interfaces, domain behavior and implementation constraints

- Consume `fulfillment.requested.v1`; transactionally persist unique `fulfillmentRequestId` and processed event before trying ERP. Use async worker with exponential backoff/jitter, max attempts, circuit breaker/bulkhead and configurable per-call timeout. Preserve queue state through restarts.
- Issue `POST /api/v1/erp/shipments` with persistent `Idempotency-Key=fulfillmentRequestId`; read `GET /api/v1/erp/shipments/{id}` for reconciliation after ambiguous timeouts; avoid blindly issuing a second effect without checking remote state.
- On confirmed response, outbox `shipment.confirmed.v1` including shipment ID and time. On terminal/permanent failure or exhausted controlled policy emit `shipment.failed.v1` and move to manual `RECONCILE_REQUIRED` state; do not silently drop.
- `GET /api/v1/fulfillments/{orderId}` returns state, attempt count, next retry, last failure reason and trace reference. Internal protected `POST /internal/v1/fulfillments/{orderId}/reconcile` logs who initiated recheck and what it did.
- Injectable ERP target address, retry policy, timeout, concurrency max and demo fault mode (fixture only). No route directly exposing the internal ERP/adapter write interface.
- Metrics: in-flight fulfillment, retries, timed-out calls, circuit-open state, adapter error rates, oldest awaiting ERP age; span links across Kafka and HTTP.

## Acceptance evidence (automate where practical)

- ERP down for a simulated five-minute interval leaves no lost requests and no request storm; attempts capped and visible.
- An ambiguous timeout followed by redelivery yields at most one ERP shipment for a fulfillmentRequestId.
- On ERP recovery, recheck/reconcile and emit a single `shipment.confirmed.v1` business outcome.
- Poisoned command becomes inspectable DLQ/reconciliation item with event ID and reason.
- Integration test proves *the same* adapter API works against container and VM endpoints by config change only.

## Recommended 64K-safe implementation slices

1. Build persistent fulfillment state machine and ERP API client with mocked server.
2. Add Kafka consumption/dedupe, confirmed/failed event outbox and trace propagation.
3. Implement bounded retries/circuit breaker + ambiguous timeout reconciliation.
4. Add operator status API, metrics, outage playbook and integration proof.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
