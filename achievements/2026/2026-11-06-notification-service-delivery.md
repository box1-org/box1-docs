# Notification service: operator notices with safe retries, delivered and live

**Date:** 2026-11-05 to 2026-11-06 (America/New_York)

**Status:** Delivered and live in `notification-service-dev`. Acceptance is partial. [box1-docs#16](https://github.com/box1-org/box1-docs/issues/16) stays open: 3 of 8 boxes are ticked with cluster proof, and the proof level of every criterion is stated in an issue comment. The other five are proven by local tests against real PostgreSQL and Kafka, or in CI, but not on the cluster.

This was a `frontier` profile run. Its run state, the decisions D-001 to D-014, the evidence, the six review-findings files and the pilot log are on branch [`agent-run/16-notification-service`](https://github.com/box1-org/box1-docs/tree/agent-run/16-notification-service/agent-runs/16-notification-service). That branch is not merged.

## Outcome

`notification-service` turns order and shipment facts that an operator would otherwise miss into notices for **named operator channels**: `ops-fulfillment` and `ops-orders`. It delivers them through a **stub** provider with bounded retries, and publishes each outcome to `box1.notification.events.v1`. By the user's decision, there are no customer recipients, no contact data and no customer identifiers anywhere in this service.

| Item | Value |
|---|---|
| Source | `box1-org/notification-service` `bacc353` ([#1](https://github.com/box1-org/notification-service/pull/1)) |
| Image | `image-registry.openshift-image-registry.svc:5000/box1-ci/notification-service@sha256:69788422d2f3beef94a255e4247ba3142f662f9edb25018489f2058edd5b363a` |
| Build | `box1-ci/notification-service-release-mpbtb`. Build and security Succeeded; promote merged the promotion PR but then failed waiting for health; smoke did not run (see Validation) |
| GitOps | `box1-workloads-dev` `ef17294`; Argo `notification-service` Synced/Healthy |
| Route | `https://notification-service-dev.apps.ocp.box1.org` |
| Contracts | `notification.delivered.v1`, `notification.failed.v1` and `NOTIFICATION.md` in `box1-ops-contracts` |

**What the service does:**
- **Inputs.** It consumes `order.state-changed.v1`, `shipment.confirmed.v1` and `shipment.failed.v1` as consumer group `notification`. It reads `order.placed.v1` at the envelope only, because that payload carries `customerId`.
- **Notice catalog** (D-002):

  | Notice | Raised by |
  |---|---|
  | `ORDER_SHIPPED` | `SHIPPED` state change or `shipment.confirmed.v1` |
  | `SHIPMENT_DELAYED` | Retryable shipment failure, which leaves the order unchanged |
  | `SHIPMENT_FAILED` | Non-retryable failure, or `EXCEPTION/SHIPMENT_FAILED` |
  | `ORDER_EXCEPTION` | Order moved to `EXCEPTION` for any other reason |
  | `ORDER_REJECTED` | Order moved to `REJECTED` |

  `COMPLETED` gives no notice. Templates are plain text, versioned `TYPE@vN`, built from allowlisted fields and escaped.
- **One fact, one notice, one delivery.** Deduplication works at three levels:
  - per event (`processed_event`);
  - per business fact (a unique dedupe key, so two events reporting one fact give one notice);
  - per delivery (the provider idempotency key and a unique receipt).
- **Delivery** runs from the database.
  - At most 6 attempts, with backoff of 2 to 32 s.
  - 503, 5xx, 408, 429 and timeouts are retried. Any other 4xx is not.
  - Exhaustion is a visible `FAILED` with a structured reason: category, code and HTTP status, never provider text.
  - Outcomes publish through a transactional outbox, keyed by `orderId`.
- **Poison records** go unchanged to `box1.notification.dlq.v1`. Replay runs inside the service on its own consumer group (`notification-replay`) and is off by default, so nothing is ever re-produced to shared topics.
- **API.** `GET /api/v1/notifications?orderId=` needs `notification-reader`. It shows status, attempts, sources, a redacted receipt (hash and length), `correlationId` and `traceparent`.
- **Stub fault control** (503, slow, permanent 4xx) needs `notification-fault-operator`.
  - Bounds: TTL at most 900 s, a call budget, and one active fault at a time.
  - Every request is audited, including refusals, with the actor and subject.
  - It is allowed only in namespaces on the allowlist; the namespace comes from the downward API.
- **Tokens.** Keycloak bearer tokens are checked per client (`azp`). The operator console's forwarded token can read but never control faults. ID tokens are refused.

## Starting baseline

- `notification-service` was the Golden Path scaffold (`3db3fbc`, template 1.1.0), onboarded by the user for this issue. It served greetings at `sha256:abc6446a…`.
- **It had no database.** PostgreSQL was off at onboarding, so `postgres.yaml` was empty and no Secret existed. The template database-credential problem tracked in [#41](https://github.com/box1-org/box1-docs/issues/41) therefore did not apply.
- **Contracts:** no `notification.*` schemas existed, and `TOPICS.md` listed the `notification` group on the fulfillment topic only.
- **Cluster:** no notification dead-letter topic and no Keycloak client.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Contracts | [box1-ops-contracts#9](https://github.com/box1-org/box1-ops-contracts/pull/9) | `4748ff5` | Two closed payload schemas with fixtures, `NOTIFICATION.md`, and the `notification` group on `box1.order.events.v1` |
| Contracts | [box1-ops-contracts#11](https://github.com/box1-org/box1-ops-contracts/pull/11) | `c2b10e4` | `box1.notification.dlq.v1` row in `TOPICS.md` (7 days, replay group) |
| Platform | [box1-gitops#75](https://github.com/box1-org/box1-gitops/pull/75) / [#80](https://github.com/box1-org/box1-gitops/pull/80) | `01cc506` / `73d482e` | KafkaTopic `box1.notification.dlq.v1`, 3 partitions. Retention cut from 14 to 7 days, so a dead-lettered `order.placed.v1` is kept no longer than on its source topic |
| Identity | [box1-gitops#76](https://github.com/box1-org/box1-gitops/pull/76) | `ad5edd6` | Public PKCE client `notification-service` with roles `notification-reader` and `notification-fault-operator` |
| Runtime | [box1-workloads-dev#94](https://github.com/box1-org/box1-workloads-dev/pull/94) | `ed5afc3` | PostgreSQL (PVC, Deployment, Service, NetworkPolicy) **with no Secret in Git**; Deployment env for the datasource, `POD_NAMESPACE` and the event floor |
| Runtime | [box1-workloads-dev#110](https://github.com/box1-org/box1-workloads-dev/pull/110) | `2c8f93c` | Event floor moved to `2026-11-06T18:03:00Z` before first start |
| Runtime | [box1-workloads-dev#113](https://github.com/box1-org/box1-workloads-dev/pull/113) | `ef17294` | Console tokens accepted for reading; stub faults allowed in `notification-service-dev` |
| Service | [notification-service#1](https://github.com/box1-org/notification-service/pull/1) | `bacc353` | Service, Flyway V1, tests, README, `docs/architecture.md`, `docs/runbook.md` |
| Promotion | [box1-workloads-dev#108](https://github.com/box1-org/box1-workloads-dev/pull/108) | `1d54764` | Digest `69788422…`, merged by the pipeline |

The user merged the first five PRs (#1, #9, #75, #76, #94). The run merged #110, #113, #11 and #80 on the user's explicit instruction.

**Made outside Git, by or with the user's approval:**
- The user created Secret `notification-service-postgres` out of band.
- Two selective Argo syncs of KafkaTopic `box1.notification.dlq.v1` in `box1-kafka` (prune off): the creation, then the 7-day retention. That Application has no automated sync.
- The user issued a Keycloak account to the run for live checks. It was used only through a PKCE login and is not recorded anywhere.

**Decisions with consequences** (records are in the run state's `decisions/`):
- **First-start offset policy (D-006).** `auto.offset.reset=earliest` plus a required `NOTIFY_EVENTS_FLOOR`. Events before the floor never become notices, so a new consumer group cannot turn retained history into a flood. The floor was set to deploy time.
- **Accepted tokens (D-007).** Access is decided by `azp`.
  - `notification-service` tokens get their own client roles.
  - `operations-console` tokens with `console-viewer` or `console-operator` get read only. This needs no change to the console.
  - Tokens from any other client get no role.
- **Database credential (D-008).** It follows the asset-service pattern: no Secret in Git and one created by the user. A managed store is #41.
- **Replay (D-006, amended in review).** Replay is group-scoped inside the service, not re-production to shared topics.

## Validation and evidence

| Test | Expected | Observed |
|---|---|---|
| Local suite on the reviewed commit, against PostgreSQL 15 and Kafka 4.2 (Testcontainers) plus the packaged app | Pass | 57 tests + 7 ITs; Checkstyle 0; SpotBugs/FindSecBugs 0 |
| Prompt scenarios, locally | Each behaves as specified | All pass: duplicate event; same fact via two events; retryable failure notice; 503 then success; permanent 4xx not retried; exhaustion → `FAILED`; poison → DLQ and replay; floor; broker outage → bounded outbox; crash after provider accept; shutdown with a retry pending, then restart (SIGTERM, prod jar); fault bounds; TTL expiry; audit immutability; namespace not allowlisted; customer-ID sentinel scan of every table, event, API response and log line |
| PR CI (`notification-service-validate-7gp7r`) | Pass | 38 + 5. Container tests run locally only, because CI has no container runtime |
| Running image | Promoted digest | Pod `imageID` `sha256:69788422…`; `/api/info` `gitRef` `bacc353` |
| Release smoke checks, run by hand through the Route | Pass | Greeting text, blank name → 400, info, all three health endpoints, OpenAPI paths, `box1_greetings_total` |
| Anonymous request or garbage token | 401 | 401 Problem JSON with `WWW-Authenticate: Bearer` |
| Reader token; console token (read) | 200 | 200, both |
| Console token on fault control | 403, audited | 403; audit row `DENIED_FORBIDDEN` |
| A real order on the cluster, plus the approved stub 503 run (`failCount` 2) | One notice; retries then success | Synthetic order with an unknown SKU → REJECTED → exactly one `ORDER_REJECTED` notice. Attempts 503, 503, then delivered; still one notice 25 s later; the fault ended after its budget, audited |
| Published event | Contract-valid, linked to the order | One `notification.delivered.v1`. Valid against contracts `main`; `traceparent` carries the order's trace ID |
| Customer-identifier scan (live) | No matches | The synthetic `customerId` appears 0 times in the API response, pod log and published event |

**Review.** Six same-model reviewer passes (architecture, persistence, messaging, security, operations, release) found **4 medium defects** that the passing tests had missed. All were fixed and the full suite was rerun:
- a late provider call could add a receipt to a notice already marked `FAILED`;
- a shutdown interrupt during a database outage could dead-letter a valid event;
- the runbook's replay produced to topics other services consume;
- Flyway's retry window exceeded the startup probe.

**Not tested on the cluster:**
- a shipment notice, because the ERP path is not established on this cluster;
- the duplicate and two-event cases;
- exhaustion and permanent 4xx;
- poison and replay;
- TTL expiry;
- a 403 for a token lacking only the reader role (the issued account holds it; CI proves it);
- load;
- rollback.

## Delivery incident

**The first rollout crash-looped** with "Failed to load config value … `notification.consumer.events-floor`".

- **Cause.** The service PR merged before its runtime PR (#94). Promotion therefore deployed the new image with no settings. The release review had flagged this ordering risk.
- **What survived.** The template pod kept serving, because `maxUnavailable` is 0. The promote task failed after its health wait, so release smoke never ran.
- **What resolved it.**
  1. Argo synced #94.
  2. The floor was moved (#110).
  3. The user created the Secret.
  4. The DLQ topic was synced. The service refuses to start without it.

## Final operational state

- **Argo `notification-service`** (automated, selfHeal, no prune) manages the service and its PostgreSQL from `box1-workloads-dev` `ef17294`, at digest `69788422…`.
- **Settings:**
  - floor `2026-11-06T18:03:00Z`;
  - console tokens accepted for reading;
  - stub faults enabled in `notification-service-dev`, each run needing approval;
  - no active fault.
- **Kafka:** `box1.notification.dlq.v1` has 3 partitions and 7-day retention. `box1-kafka` is Synced.
- **Manual resources outside Git:** the database Secret and the two topic syncs.
- **Data left on the cluster:** one synthetic order (`ord_b84bd53f…`, REJECTED) in order-service, and its notice.
- **Idle resource use:** about 229Mi for the service (512Mi limit) and 38Mi for PostgreSQL.

## Recovery and follow-ups

- **Roll back** by reverting the promotion commit (#108) in `box1-workloads-dev`. Argo `selfHeal` reverts any manual change. Flyway V1 only creates new tables. This rollback has not been exercised.
- **Operator procedures** are in the service's `docs/runbook.md`:
  - DLQ replay through the `notification-replay` channel;
  - re-notifying a period (group offset reset plus floor, each step approved);
  - fault control;
  - Secret rotation;
  - recovery.
- **Open on #16:** five criteria still need cluster proof (see the issue comment for each proof level).
- **Follow-ups, none blocking and none filed as separate issues yet:**
  - expose `actor_subject` in the fault audit API (stored, not returned);
  - a promote-task check that runtime prerequisites exist before a promotion merges (platform change);
  - alerts once [#22](https://github.com/box1-org/box1-docs/issues/22) lands;
  - a separate migration owner for the audit trigger, with [#41](https://github.com/box1-org/box1-docs/issues/41).
- **The run-state branch** has not been merged to `main`.
