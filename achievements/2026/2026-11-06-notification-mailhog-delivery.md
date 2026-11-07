# Notification service: operator notices delivered as real email to MailHog

**Date:** 2026-11-06, 21:00–22:30 EST (America/New_York); merges between 2026-11-07 02:17 and 03:28 UTC

**Status:** Delivered and live. Since 21:44 EST, `notification-service` in `notification-service-dev` sends every operator notice as a real SMTP message to **MailHog**, an in-cluster mail sink managed by GitOps. Real order traffic has already produced messages in MailHog. The cluster acceptance checks through the service API, events and a fault run were **not run**; the user deferred them. [box1-docs#16](https://github.com/box1-org/box1-docs/issues/16) stays open and no checkbox changed.

Background: [2026-11-06 notification service delivery](2026-11-06-notification-service-delivery.md), which built the service with a stub provider.

## Outcome

Before this change, a "delivered" notice was only a stub receipt (a hash) that operators could not see. Notices now arrive as email in mailboxes that operators can open:

```text
order/shipment event → notification-service → SMTP → MailHog → web UI and API (https://mailhog.apps.ocp.box1.org)
```

| Notice | Mailbox |
|---|---|
| `ORDER_SHIPPED`, `SHIPMENT_DELAYED`, `SHIPMENT_FAILED` | `ops-fulfillment@box1.local` |
| `ORDER_EXCEPTION`, `ORDER_REJECTED` | `ops-orders@box1.local` |

- **Sender:** `box1-notifications@box1.local`.
- **Subject:** `[Box1] <Title> — <orderId>`.
- **Headers:** Message-ID `<notificationId@box1.local>`, plus `X-Box1-Notification-Id`, `X-Box1-Notice-Type`, `X-Box1-Order-Id` and `X-Box1-Template-Version`.
- **Body:** the existing versioned template text, then notice type, order, notification ID, template version and correlation ID. Messages carry internal operational identifiers only.
- **Meaning of `DELIVERED`:** the message was **accepted by MailHog**, not read by a person. No message leaves the cluster.

## Starting baseline

- `notification-service` `24dda0f` ran with the `stub` provider only. `StartupChecks` refused every other provider.
- Fault control lived inside the stub at `/api/v1/stub/faults`.
- The event contracts allowed only `provider: "stub"` in `notification.delivered.v1` and `notification.failed.v1`.
- No mail sink existed on the cluster.
- The release template declared a `SCAN_OUTPUT` pipeline result while `security-gates: disabled`. This was not known to be a problem at the start.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| box1-ops-contracts | [#12](https://github.com/box1-org/box1-ops-contracts/pull/12) | `bb381b0` | Adds `mailhog` to the `provider` enum of both notification events; documents both providers in `NOTIFICATION.md` |
| box1-gitops | [#91](https://github.com/box1-org/box1-gitops/pull/91) | `491dcaf` | `platform/mailhog` and the Argo Application `mailhog` |
| box1-gitops | [#92](https://github.com/box1-org/box1-gitops/pull/92) | `e07852a` | Fixes the console-links file that #91 broke (see Validation) |
| notification-service | [#3](https://github.com/box1-org/notification-service/pull/3) | `38b4d8b` | MailHog provider, provider boundary, `/api/v1/delivery-faults`, schema V2 |
| notification-service | [#4](https://github.com/box1-org/notification-service/pull/4) | `fc28514` | Release `security-gates: disabled` → `gate` |
| box1-workloads-dev | [#142](https://github.com/box1-org/box1-workloads-dev/pull/142) | `932b1ba` | `NOTIFY_PROVIDER=mailhog` and SMTP settings (merged by the user) |
| box1-workloads-dev | [#143](https://github.com/box1-org/box1-workloads-dev/pull/143), [#145](https://github.com/box1-org/box1-workloads-dev/pull/145) | `1aac5c8`, `6331d80` | Image promotions by the release pipeline |

**MailHog (box1-gitops `platform/mailhog`):**

- **Image:** `mailhog/mailhog` v1.0.1 pinned by digest `sha256:8d76a3d4…` (amd64). It uses Maildir storage on PVC `mailhog-maildir` (1 GiB, `lvms-vg1`), so the mailbox survives a pod restart. The Deployment strategy is `Recreate`.
- **SMTP:** Service `mailhog`, port 1025, cluster-internal, no authentication and no TLS. The NetworkPolicy admits SMTP only from `notification-service-dev`.
- **Web UI and API:** MailHog listens on loopback only. An `ose-oauth-proxy-rhel9` sidecar, the same digest the cluster already runs in `openshift-storage`, is the only way in. It is reached through Service `mailhog-web` on port 8025 and the reencrypt Route.
  - Login needs `get` on that Service.
  - A bearer token with the same permission works through `--openshift-delegate-urls`, which needs a ClusterRoleBinding to `system:auth-delegator`.
  - The proxy's cookie secret is generated at each pod start, so no secret is stored in Git.
- **Console:** the link "MailHog (operator notices)" appears in the box1 Platform menu.

**notification-service:**

- **Provider boundary.** The worker calls one boundary, which:
  - returns the existing receipt if there is one;
  - otherwise applies the bounded fault decision;
  - then calls the configured provider (`mailhog` or `stub`).

  Failed attempts therefore never create a message. A call that is still running after a worker timeout is not started twice.
- **`MailHogProvider`** sends over SMTP with Angus Mail (version from the Quarkus BOM) and a 1.5 s connect, read and write timeout. Outcomes map as follows:

  | SMTP outcome | Recorded as | Retried |
  |---|---|---|
  | Connection failure, timeout | `PROVIDER_ERROR` / `PROVIDER_TIMEOUT` | Yes (transient) |
  | 4xx reply | 503 | Yes (transient) |
  | 5xx reply | 422 | No (permanent) |

  No SMTP server text is stored.
- **API.** `/api/v1/delivery-faults` replaces `/api/v1/stub/faults` and keeps the same roles, bounds and audit. The old paths remain as deprecated aliases.
- **Schema V2** adds `delivery_receipt.message_id` and `recipient`, with operator-only checks, and a provider check of `stub` or `mailhog`. The read API exposes both fields.
- **Default provider.** The image default stays `stub`, so an image never depends on SMTP settings it was not deployed with. The cluster selects `mailhog` through `NOTIFY_PROVIDER`.

**Tradeoff:** MailHog has no idempotency key. If the process dies after MailHog accepted a message but before its receipt is committed, the next attempt sends a second copy with the same Message-ID. This is documented in the service's `docs/architecture.md`.

**Unplanned finding: release false failure.** Every notification-service release had ended `CouldntGetPipelineResult: invalid pipelineresults [SCAN_OUTPUT]`.

- **Cause.** The template exposes the security task's `SCAN_OUTPUT` result. `box1-security-gates` writes it only when an RHACS scan produced a summary ([#57](https://github.com/box1-org/box1-docs/issues/57)). With gates `disabled`, no scan ran, so the result never existed.
- **Effect in `v4q5h`.** That run was a pure false failure: all tasks succeeded and the image was promoted.
- **Fix.** #4 switches the release to `gate` mode, matching the other Box1 services. A policy violation can now block a notification-service release.

## Validation and evidence

**Local and CI (before merge):**

| Check | Result |
|---|---|
| `./mvnw verify` (CI profile) | 43 tests pass; checkstyle clean; SpotBugs/FindSecBugs 0 findings |
| `MailHogDeliveryTest` (Testcontainers PostgreSQL 15, Kafka 4.2.0, MailHog at the cluster digest) | 7/7 pass (details below) |
| `ScenariosTest`, `SecurityTest` | 17/17 and 6/6. `ScenariosTest` passed on a rerun; the first attempt hit a Postgres container launch failure in the local container runtime |
| Contract test | Produced `mailhog` events validate against box1-ops-contracts `bb381b0` |
| PR validation pipelines | Passed for #3 and #4 |

`MailHogDeliveryTest` showed:

- one message per notice, in the right mailbox, with the expected From, To, Subject and Message-ID;
- a sentinel `customerId` absent from the message;
- `provider=mailhog` in the receipt and in `notification.delivered.v1`;
- a duplicate source event gives one message;
- `TRANSIENT_503` ×2 gives 3 attempts and one message;
- `PERMANENT_4XX` gives `FAILED` and no message;
- a hung SMTP server gives `PROVIDER_TIMEOUT` retries, then one message.

**Cluster:**

| Check | Expected | Observed |
|---|---|---|
| MailHog GitOps sync | Synced/Healthy | Argo `mailhog` Synced/Healthy at `491dcaf`; pod 2/2, 0 restarts; PVC Bound |
| TLS on the Route | Trusted | `ssl_verify_result` 0 |
| Anonymous or garbage-token request | Refused | 403 with the "Log in with OpenShift" sign-in page |
| Cluster-admin bearer token (`oc whoami -t`) | API access | 200 from `/api/v2/messages` |
| Release with gate mode | Run succeeds | `notification-service-release-rksgd` **Succeeded** (details below) |
| Provider selection | `mailhog` | Startup log `Events floor 2026-11-06T18:03:00Z; provider mailhog`; 1/1 ready, 0 restarts |
| Real delivery | Mail in MailHog | **5 messages** from real order traffic, 21:45:44–22:25:51 EST: all `ops-fulfillment@box1.local`, subject `[Box1] Order shipped — ord_…`, sender `box1-notifications@box1.local`, five distinct notification IDs (one per order). Their arrival also shows SMTP from `notification-service-dev` passes the NetworkPolicy |

The `rksgd` release in detail:

- `policy=pass`;
- `SCAN_OUTPUT` reported critical 0, high 10, medium 159, low 79;
- the SBOM was uploaded to RHTPA;
- promotion #145 merged and Argo `notification-service` became Synced/Healthy.

**Not tested on the cluster:**

- the read API showing `provider=mailhog` and `messageId`;
- `notification.delivered.v1` on Kafka with `provider=mailhog`;
- a fault run through `/api/v1/delivery-faults`;
- a cluster scan for customer identifiers in the messages;
- SMTP refused from other namespaces;
- browser login to the MailHog UI.

All of these need a reader token or a fault run, and the user deferred them.

**Regression introduced and fixed.** #91 appended the MailHog console link to a file with no trailing newline. The `---` separator joined the previous line, kustomize failed, and the `console-links` Application showed a ComparisonError. Nothing was pruned. #92 fixed it, and `console-links` is Synced/Healthy at `e07852a` with all five links.

## Final operational state

| Item | Value | Managed by |
|---|---|---|
| MailHog | Namespace `mailhog`; `https://mailhog.apps.ocp.box1.org`; SMTP `mailhog.mailhog.svc.cluster.local:1025` | Argo CD `mailhog` (box1-gitops `platform/mailhog`, automated sync with prune) |
| notification-service | Image `sha256:68d42dfd…` from `fc28514`; `NOTIFY_PROVIDER=mailhog` | Argo CD `notification-service` at box1-workloads-dev `6331d80` or later |
| Release pipeline | `security-gates: gate` | notification-service `.tekton/release.yaml` |
| Fault API | `/api/v1/delivery-faults`; `/api/v1/stub…` kept as deprecated aliases | Service code |

The service and MailHog run from source `main`, with no manual overrides. The `notification.stub.*` setting names and `stub_fault*` table names are kept from v1 for compatibility.

## Recovery and follow-ups

**Recovery:**

- **Back to receipts only:** set `NOTIFY_PROVIDER=stub` in box1-workloads-dev. Do this before rolling back to an image older than `38b4d8b`, because older images refuse `mailhog`. Flyway V2 only adds nullable columns and a check; older images ignore future migrations.
- **MailHog down:** deliveries retry as transient and end `FAILED`/`RETRIES_EXHAUSTED` after 6 attempts. Restore the pod; the Maildir PVC keeps the mailbox.
- **Remove MailHog:** switch the provider to `stub` first, then delete `applications/mailhog.yaml`.
- **Untested:** none of these recovery paths has been exercised on the cluster.

**Follow-ups:**

- [box1-docs#95](https://github.com/box1-org/box1-docs/issues/95) "Update mailhog with mailpit" (open, filed by the user at 21:38 EST). It would replace MailHog v1.0.1 with Mailpit; MailHog's last release dates from 2020. The provider code is plain SMTP and should need configuration changes only. Not started.
- [box1-docs#16](https://github.com/box1-org/box1-docs/issues/16): live acceptance through the API, events and one `TRANSIENT_503` run, then remove the `/api/v1/stub` aliases once no caller uses them.
- [box1-docs#57](https://github.com/box1-org/box1-docs/issues/57): any gate or observe release whose scan returns no summary fails the same way. `CouldntGetPipelineResult` can also hide a real task failure, as in runs `mpbtb` and `6x952`, where promote actually failed.

**Correction.** Comments on #16 and #57, and the notification-service#4 commit message, said runs `mpbtb`, `6x952` and `v4q5h` all had every task succeed. Only `v4q5h` did. Follow-up comments on both issues correct this.
