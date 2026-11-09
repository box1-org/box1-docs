# agentic-operations reads traces, logs and alerts as evidence

**Date:** 2026-11-08 to 2026-11-09 (America/New_York)

**Backlog:** [box1-docs#111](https://github.com/box1-org/box1-docs/issues/111). This resolves #20's open question Q-6, and follows up [#82](https://github.com/box1-org/box1-docs/issues/82).

**Status:** Delivered.

| Evidence | How it was verified |
|---|---|
| Traces | Observed live: `TRACE_CONTENT` OK in a real analysis. |
| Logs and alerts | Working **as reported by the user** after the two fixes below. Every precondition was verified on the cluster (RBAC, visible projects, port). The fixed result itself was not read back here: the pod that served the user's re-run was replaced before it could be checked. |
| Telemetry alerts from asset-service | **Deferred** (Q-5). |

## Outcome

Incident analyses, and the console Assistant's answers, now cite real platform evidence for an order:

- **`TRACE_CONTENT`:** a Tempo trace summary with services, root span, duration, and error and slowest spans.
- **`LOGS`:** LokiStack log lines for the order from the order-path services.
- **`METRICS_AND_ALERTS`:** Alertmanager active alerts, plus Thanos `up` (scrape targets down) for those namespaces.

agentic-operations reads them with **its own ServiceAccount**, through a projected token, read-only. RBAC limits it to the eight Box1 service namespaces.

MCP clients and the Assistant also get three tools: `get_trace`, `search_logs` and `list_service_alerts`.

The Assistant's policy now says that only an `OK` read counts as checked. This fixes an overstatement seen in the [Assistant chat log](2026-11-08-console-assistant-chat.md).

```text
agentic-operations  5ff4a17 (evidence code, live 2026-11-08); now 8ad728e, image sha256:fe9f3ed5…fa1631
cluster RBAC        box1-gitops 9bf4fdc, then c073f3c (observability-tracing / observability-logging, manual sync)
namespace RBAC/env  box1-workloads-dev b15b244, then d76b898
```

## Starting baseline

Every analysis listed four sources as `UNAVAILABLE`. `EvidenceService.gather()` hard-coded them:

- `TRACE_CONTENT`: "no trace read access in v1 (Q-6)"
- `METRICS_AND_ALERTS`: "no metrics or alert read access in v1 (Q-6)"
- `LOGS`: "no centralized logging (#82)". LokiStack had since been delivered ([log](2026-11-06-loki-centralized-logging.md)).
- `TELEMETRY_ALERTS`: asset-service grant not provisioned (Q-5).

The service had no way to read these sources:
- it sent no token upstream;
- `automountServiceAccountToken: false` was set on its ServiceAccount and Deployment;
- no RBAC granted it anything;
- the `tempo-box1` NetworkPolicy blocked its namespace.

**User decisions, 2026-11-08:**
- the service uses its **own identity**;
- metrics and alerts are read **per Box1 namespace** through the monitoring tenancy ports, not cluster-wide;
- telemetry alerts are **deferred**.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `box1-gitops` | [#110](https://github.com/box1-org/box1-gitops/pull/110) | `9bf4fdc` | See below. |
| `box1-workloads-dev` | [#162](https://github.com/box1-org/box1-workloads-dev/pull/162) | `b15b244` | See below. |
| `agentic-operations` | [#6](https://github.com/box1-org/agentic-operations/pull/6) | `5ff4a17` | See below. |
| `box1-gitops` | [#115](https://github.com/box1-org/box1-gitops/pull/115) | `c073f3c` | **Fix found live:** `box1-observability-reader` also gets `namespaces` get, so the Box1 projects become visible to the LokiStack gateway, and `metrics.k8s.io` `pods` get, which the Thanos tenancy proxy checks. |
| `box1-workloads-dev` | [#164](https://github.com/box1-org/box1-workloads-dev/pull/164) | `d76b898` | **Fix found live:** the Alertmanager tenancy port is **9092**, not 9095. |
| `box1-workloads-dev` | #163 | auto | Promotion of `5ff4a17`. |

**box1-gitops#110**
- `ClusterRoleBinding` `box1-agentic-operations-traces-read-dev` binds the existing `box1-traces-read-dev`.
- `tempo-box1` NetworkPolicy: an ingress rule for agentic-operations pods on 8080.
- `ClusterRoleBinding` `box1-agentic-operations-application-logs` binds the operator-shipped `cluster-logging-application-view`.
- New ClusterRole `box1-observability-reader`: pods get/list and pods/log get. It is bound only through RoleBindings.

**box1-workloads-dev#162**
- agentic-operations:
  - a projected ServiceAccount token (1 h, rotated) at `/var/run/secrets/box1/platform/token`; automount stays off;
  - a ConfigMap with the injected service CA;
  - the Tempo, LokiStack, Thanos and Alertmanager URLs.
- In each of the 8 Box1 `-dev` namespaces: RoleBindings to `box1-observability-reader` and `monitoring-rules-view`.

**agentic-operations#6**
- **`PlatformClient`:** reads the bearer token from the file and re-reads it on rotation. TLS trusts only the service CA. It is bounded like the other upstreams. When unconfigured it returns `UNAVAILABLE` and makes no request.
- **Reads:** Tempo `/api/traces`, LokiStack `query_range` on the MDC `orderId`/`traceId`, and the Alertmanager and Thanos tenancy ports. Queries are built only from validated IDs and a namespace allowlist set in config.
- **`PlatformShapes`:** flattens results to named fields of 256 characters or fewer.
- These sources are not CORE: a failure is shown, but never degrades an analysis.
- **New tools:** `get_trace`, `search_logs` and `list_service_alerts`.
- **Chat policy `aiops-chat-policy-2`.**

**Manual Argo CD syncs.** The user approved them, on 2026-11-08, for `observability-tracing` and `observability-logging`. Before each sync, the only resources out of sync were the ones above, plus the documented `logging-loki-s3-sync` Job on the second logging sync.

## Validation and evidence

**Local tests**
- agentic-operations `./mvnw verify` passed 97 tests.
- `PlatformEvidenceTest`, 5 tests:
  - an analysis cites trace, logs and alerts;
  - a refused or missing source is typed and does not degrade the analysis;
  - an unconfigured source says so and reads nothing;
  - MCP refuses bad arguments with no read;
  - injected log text reaches the model only inside the untrusted envelope.
- `HttpUpstreamsPlatformTest`, 5 tests:
  - the bearer comes from the token file and follows rotation;
  - nothing is sent when unconfigured;
  - 403, oversize and non-JSON responses are typed;
  - exact query strings are built, and namespace, field and value injections are rejected;
  - the shapes drop unnamed fields.

**Least privilege**, checked with `oc auth can-i` and SubjectAccessReviews as `system:serviceaccount:agentic-operations-dev:agentic-operations`:

| Access | Result |
|---|---|
| pods/log and prometheusrules in Box1 namespaces | yes |
| Tempo `dev` traces | allowed |
| Loki `application` logs | allowed |
| pods/log in `openshift-monitoring` | no |
| pods in `keycloak` | no |
| secrets in Box1 namespaces and its own namespace | no |
| pods/exec | no |
| list namespaces | no |
| prometheusrules in `openshift-monitoring` | no |

**First live analysis** (run by the user):

| Item | Result |
|---|---|
| `TRACE_CONTENT` (`ev_11`) | **OK**, trace `ad6c955c…` |
| `METRICS_AND_ALERTS` | **TIMEOUT** |
| `LOGS` | **UNAUTHORIZED** |

`aiops_evidence_fetch_total` showed:
- `METRICS_AND_ALERTS` TIMEOUT ×3, which were the Alertmanager reads;
- `METRICS_AND_ALERTS` UNAUTHORIZED ×3, which were the Thanos `up` reads;
- `LOGS` UNAUTHORIZED.

**Diagnosis:**
- **Alertmanager:** Service `alertmanager-main` exposes web 9094, tenancy **9092** and metrics 9097. Nothing listens on 9095.
- **Thanos:** the tenancy proxy checks `get` on `metrics.k8s.io` pods, and the SubjectAccessReview returned false.
- **LokiStack:** the application-log RBAC was allowed, but `oc get projects --as=<SA>` showed none of the Box1 namespaces. The gateway lists the caller's projects to decide which namespaces it may read.

**After the fixes:**

| Check | Result |
|---|---|
| `oc get projects --as=<SA>` | exactly the 8 Box1 projects, plus one visible to every authenticated user |
| SubjectAccessReview `metrics.k8s.io` pods in `order-service-dev` | true |
| Deployment Alertmanager URL | ends in `:9092` |
| Pod | new pod running |

The user re-ran an analysis and reported that it worked. That run could not be read back: agentic-operations `8ad728e` was promoted at 00:49 UTC (box1-workloads-dev#192, unrelated Dev Spaces files) and replaced the pod, so the in-memory results and counters were lost.

**Not verified:**
- content during a real firing alert;
- trace and log volume limits under load;
- whether the real model follows `aiops-chat-policy-2`.

## Final operational state

- **agentic-operations** (Argo CD, `box1-workloads-dev`) runs `8ad728e`, which includes this work. It has the projected token, the service CA and the platform URLs, with Alertmanager on 9092.
- **Cluster RBAC and the Tempo NetworkPolicy:** `observability-tracing` and `observability-logging` in `box1-gitops`. Both are **manual-sync**, and both were synced.
- **Namespace RoleBindings:** each service's directory in `box1-workloads-dev`, auto-synced.
- **Telemetry alerts** remain `UNAVAILABLE`.
- **agentic-operations-dev's own logs** are not collected into LokiStack.

## Recovery and follow-ups

To withdraw access, revert any of the following. The service then reports these sources as `UNAVAILABLE` or `UNAUTHORIZED`; nothing else depends on them.
- box1-workloads-dev#162 and #164: removes the token, the URLs and the RoleBindings.
- box1-gitops#110 and #115: removes the bindings, the role and the Tempo ingress rule. This needs a manual sync, with prune, of the two Applications.

None of these was exercised.

**Follow-ups:**
- Telemetry alerts from asset-service: Q-5 on [#20](https://github.com/box1-org/box1-docs/issues/20) (a confidential client and `ASSET_READ_CLIENTS`).
- Collect `agentic-operations-dev` logs.
- A live check during a real firing alert.
- Durable analyses ([#97](https://github.com/box1-org/box1-docs/issues/97)), so a rollout does not lose results under review.
