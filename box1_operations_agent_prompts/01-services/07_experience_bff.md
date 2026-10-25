# Service 07 — Experience / BFF service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P1 · FR-04/08; NFR-01/02/09

**Dependencies:** Order, inventory, fulfillment, telemetry, notification APIs and authenticated user identities.

## Mission and boundary

Provide a cohesive, role-aware HTTP backend for the console so browsers do not need individual internal service routes. Proposed repo `box1-org/box1-ops-bff`. Treat this as a projection/orchestration boundary only; it **must not own** authoritative order/inventory state or copy secrets into frontend responses.

## Interfaces, domain behavior and implementation constraints

- `GET /api/v1/overview`: aggregate counters for submitted, stuck, shipped, exception orders, active equipment alerts, recent incidents; indicate data source freshness and partial failures.
- `GET /api/v1/orders/{orderId}/summary`: join approved API projections (never cross-database SQL) for status, reservation state, fulfillment attempts, notification outcome, timeline, diagnostic trace IDs and change links.
- `GET /api/v1/incidents/{incidentId}/evidence` for curated read-only incident evidence from telemetry/observability adapters; when an upstream dependency fails return partial result with `sourceStatus`, not invented values.
- Auth: OIDC JWT verification at BFF, role checks for customer/operator/developer/admin, downstream least-privilege service identity; only return a customer's own orders. Use installed identity provider if available, otherwise a secure documented local-test fake identity, never public anonymous production API.
- Strict timeouts, connection pooling, bulkheading, bounded concurrent queries, cache TTL and explicit staleness; use Problem JSON and stable pagination.
- W3C trace propagation to downstream REST clients; structured logs (request IDs, role, path) without bearer token/PII. Include resilience integration tests for one dependency slow/unavailable.
- CORS and CSRF strategy documented; expose a single suitable TLS Route under `apps.ocp.box1.org` through GitOps only.

## Acceptance evidence (automate where practical)

- One order summary includes expected immutable IDs, statuses, time stamps and evidence links.
- Unauthorized role/customer access is denied even if the UI manually calls hidden endpoints.
- Upstream timeout yields a bounded partial response and clear failed-source badge, not infinite loading.
- No public exposure of service-admin endpoints or tokens; trace/correlation IDs are continuous from browser to service.

## Recommended 64K-safe implementation slices

1. Auth middleware and API aggregation with mocked upstreams.
2. Order summary/read models and partial-failure semantics.
3. Incident/overview projection with tracing and query resilience.
4. Backend security/contract tests and approved Route via GitOps.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
