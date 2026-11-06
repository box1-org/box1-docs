# Service 06 — Notification service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#16](https://github.com/box1-org/box1-docs/issues/16).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P1 · FR-07, DAT-04/05; NFR-02/07

**Dependencies:** order and shipment events, the Keycloak `box1` realm, and a **stub** delivery backend rather than a real email/SMS provider.

## Mission and boundary

Own asynchronous delivery requests, attempts and failure status. Proposed repo `box1-org/box1-ops-notification`. This exists to demonstrate safe retries, consumer replay and operator visibility; do not demand paid third-party integrations.

**Operator notices only (user decision, 2026-11-05).** Notices go to named operator channels, not to customers. No service in Box1 holds customer contact details, and this one must not start: there are no customer recipients, no contact data, and no customer identifiers in notices, receipts, events or logs.

Notices exist to surface what operators would otherwise miss. For example, under `ORDER-STATE.md` a `shipment.failed.v1` with `retryable=true` changes no order state and only adds a timeline note; this service turns it into a notice.

## Interfaces, domain behavior and implementation constraints

- **Inputs.** Consume `order.state-changed.v1` (for example `toState` `EXCEPTION`, `REJECTED`, `SHIPPED`, `COMPLETED`), `shipment.failed.v1` (retryable and not), and `shipment.confirmed.v1`. The exact notice catalog is a design decision. `notification.requested.v1` stays in the topic contract but is out of scope until a producer exists. Transform through versioned templates and persist notification intent.
- **Recipient.** A configured, named operator channel (for example `ops-fulfillment`), mapped from notice type. No personal data.
- Model `notificationId`, `orderId`, `channel`, `noticeType`, `templateVersion`, `status`, `attemptCount`, timestamps, dedupe key and structured failure reason. The idempotency/deduplication key is derived from the business fact (`orderId`, notice type and the triggering state or failure), not from event arrival: the same fact redelivered, or reported by two events (a `SHIPPED` state change and a `shipment.confirmed.v1`), gives one intent and one effective delivery.
- **Stub provider.** The default `stub` provider writes deterministic, redacted delivery receipts that the operator API returns. Real providers are pluggable but disabled until explicit secret provisioning and user approval. Stub fault modes (transient 503, slow response, permanent 4xx) are switched by configuration or a control endpoint, each bounded by a TTL, audited with the actor from the token, and refused unless the namespace is on the demo allowlist named by the user, per `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`.
- **Retry and failure.** Bounded retry with backoff; a permanent 4xx is not retried; exhaustion is a visible `FAILED` status with a sanitized reason. Consumer records the service cannot process go unchanged to a notification dead-letter topic with an operator replay procedure. Publish `notification.delivered.v1` / `notification.failed.v1` through a transactional outbox to `box1.notification.events.v1`.
- **API.** `GET /api/v1/notifications?orderId=` for authorized operators, with Keycloak bearer tokens and a reader role. Decide up front which client tokens it accepts, so the operator console backend (`08_operator_console.md`) can call it without a later change to this service. The stub fault control needs a separate role. Keep the Golden Path smoke endpoints working so release smoke passes.
- Unit tests for template escaping/injection, permanent 4xx versus transient failure, duplicate consumption, poison inputs, shutdown while retry pending.
- Metrics for pending age, delivery success/error counts and retry exhaustion; trace links to business order.

## Acceptance evidence (automate where practical)

- One shipped-order event processed twice creates one intent and one effective delivery.
- Stub 503/retry demonstration shows increasing attempts and eventual success or visible failure; no infinite retry loop.
- Operator query accurately displays status and sanitized failure reason.
- No customer identifiers appear in notices, receipts, logs or event payloads.
- The same business fact reported by two different events creates one intent and one effective delivery.
- A retryable `shipment.failed.v1`, which leaves the order unchanged, still produces an operator notice.
- An anonymous API request gets 401 and a token without the reader role gets 403; the stub fault control is refused outside an allowlisted namespace and expires on its TTL.
- Consumer poison records reach the notification dead-letter topic, with a documented replay procedure.

## Recommended 64K-safe implementation slices

1. Data model + stub provider and query endpoint.
2. Kafka consumer + idempotent notification intents and outbox.
3. Template versioning, bounded retries, failure handling.
4. Metrics, UI projection integration and CI tests.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** this service, its contracts, manifests and documentation. Showing notices in the operator console is #18's work, and changes to any other service are out of scope; a needed change there is a stop condition. **Background:** the earlier pilots' `pilot-log.md` files. The order and inventory runs set the consumer, outbox and dead-letter patterns; the telemetry run (#15) set the bounded, audited fault-control pattern.

**Discovery must cover (state observed 2026-11-05 America/New_York; verify before relying on it):**

- the repository: no notification repository existed. Onboarding one through the Golden Path is an approval-required action for the user; confirm its name (`box1-ops-notification` was only proposed);
- the deployment pattern: the template adds `postgres.yaml` with the database credential issue tracked in [#41](https://github.com/box1-org/box1-docs/issues/41); the release smoke task needs unauthenticated `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi` and `/q/metrics` ([#40](https://github.com/box1-org/box1-docs/issues/40));
- Kafka: the internal listener is plaintext with no client authentication. `box1.notification.events.v1` exists in `box1-gitops/platform/kafka/topics/notification.yaml`. Dead-letter topics exist for order, inventory, fulfillment and telemetry, **not** for notification;
- contracts in `box1-ops-contracts`: no `notification.*` event schemas exist. `TOPICS.md` lists consumer group `notification` on `box1.fulfillment.events.v1` only, not on `box1.order.events.v1`. `order.state-changed.v1` carries `orderId`, `fromState`, `toState`, `reasonCode`, `changedAt`; `shipment.failed.v1` carries `retryable` and `reasonCode`; only `order.placed.v1` carries `customerId`;
- reusable patterns: the order service's SmallRye Kafka consumers with `failure-strategy=dead-letter-queue` and its transactional outbox; the Keycloak bearer configuration in `fulfillment-adapter` and `asset-service`;
- Keycloak: realm `box1` in `box1-gitops/platform/identity/keycloak/realm/`. The operator console run proposes client `operations-console` with roles `console-viewer` and `console-operator` (#18 run, decision D-002). `asset-service` requires `azp=asset-service`, which blocked the console from reading it; the operator does not create client roles from `spec.roles` ([#59](https://github.com/box1-org/box1-docs/issues/59)).

**Design decisions to record before implementation:**

- the notice catalog: which events and states produce which notice type and channel, and the template versioning scheme;
- the dedupe key, including how one fact reported by two events maps to one intent;
- retry and backoff limits, and which stub responses count as permanent;
- the outbox, publish ordering and the partition key (`orderId`);
- Kafka offset policy on first start, so a new consumer group does not replay a week of history into notices, or does so deliberately;
- the contracts PRs: `notification.delivered.v1` and `notification.failed.v1` schemas, and adding the `notification` group to `box1.order.events.v1` in `TOPICS.md`;
- the notification dead-letter topic, a shared-infrastructure PR that needs approval;
- the Keycloak client and roles, and which tokens the read API accepts so the console can use it. A GitOps PR that needs approval; check the roles exist after sync (#59);
- the database credential while #41 is open;
- stub fault control: modes, bounds, TTL, audit and the allowlist; the demo namespace is named by the user;
- retention of intents, attempts and receipts.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | Notification schemas and the `TOPICS.md` change reviewed in `box1-ops-contracts` |
| 3 Implementation | Fault-control limits enforced server-side; no customer identifier reaches a template, receipt, event or log |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs; the Security pass covers the API, fault control and logs |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | A real order's shipment or failure on the cluster produces one notice visible through the API; one stub 503 run shows retries then success, after approval |

**Verification scenarios:** duplicate event; the same fact through two events; retryable shipment failure produces a notice; stub 503 then recovery; stub permanent 4xx not retried; retry exhaustion gives `FAILED`; poison record reaches the dead-letter topic and replays; shutdown with a retry pending resumes without a duplicate delivery; template injection is escaped; scan of logs, receipts and payloads finds no customer identifier; anonymous request; request without the reader role; fault control outside the allowlist; fault TTL expiry; broker outage gives a bounded outbox backlog and later delivery.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
