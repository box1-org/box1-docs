# Service 06 — Notification service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P1 · FR-07, DAT-04/05; NFR-02/07

**Dependencies:** Order/shipment events and a **stub** delivery backend rather than a real email/SMS provider.

## Mission and boundary

Own asynchronous delivery requests, attempts and failure status. Proposed repo `box1-org/box1-ops-notification`. This exists to demonstrate safe retries, consumer replay and operator visibility; do not demand paid third-party integrations.

## Interfaces, domain behavior and implementation constraints

- Consume `order.state-changed.v1` and `shipment.confirmed.v1` or explicit `notification.requested.v1`, transform through versioned templates and persist notification intent.
- Model `notificationId`, `orderId`, `channel`, `templateVersion`, `status`, `attemptCount`, timestamps, dedupe key and structured failure reason. A message has an idempotency/deduplication key derived from notification intent, not event arrival count alone.
- Default `stub` provider writes redacted deterministic delivery receipts. Make real providers pluggable but disabled until explicit secret provisioning and user approval. Never include full personal email/mobile details in Kafka or test logs.
- Bounded retry/backoff and dead-letter/deferred queue; `notification.delivered.v1` / `notification.failed.v1` outbox. `GET /api/v1/notifications?orderId=` for authorized operators.
- Unit tests for template escaping/injection, permanent 4xx versus transient failure, duplicate consumption, poison inputs, shutdown while retry pending.
- Metrics for pending age, delivery success/error counts and retry exhaustion; trace links to business order.

## Acceptance evidence (automate where practical)

- One shipped-order event processed twice creates one intent and one effective delivery.
- Stub 503/retry demonstration shows increasing attempts and eventual success or visible failure; no infinite retry loop.
- Operator query accurately displays status and sanitized failure reason.
- Forbidden customer identifiers don't leak to logs or event payloads.

## Recommended 64K-safe implementation slices

1. Data model + stub provider and query endpoint.
2. Kafka consumer + idempotent notification intents and outbox.
3. Template versioning, bounded retries, failure handling.
4. Metrics, UI projection integration and CI tests.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
