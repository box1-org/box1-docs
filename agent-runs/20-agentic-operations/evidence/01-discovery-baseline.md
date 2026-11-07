# Phase 0 discovery baseline

Observed 2026-11-06 21:50–22:20 EST (America/New_York). Everything here was read-only: `gh api` against `main`, `oc get`, `oc describe`, and one `GET /v1/models` (see the vLLM section). No Secret values were read.

## Revisions

| Repository | main |
|---|---|
| box1-docs | `12f0b11` (prompt merged, PR #96) |
| box1-workloads-dev | `932b1ba` |
| box1-gitops | `b71a407` |
| box1-templates | `badc3c3` |
| box1-ops-contracts | `bb381b0` |
| operations-console | `9a87948` |
| asset-service | `c75b6dc` |
| notification-service | `38b4d8b` |
| scenario-controller | `23125f8` |
| order-service | `64362af` |

## Target repository

- `box1-org/agentic-operations` does not exist (`gh repo view`: "Could not resolve to a Repository"). There is no `applications/agentic-operations.yaml` in box1-workloads-dev.
- Golden Path template `quarkus-rest-service` (box1-templates `badc3c3`):
  - The name pattern rejects a `box1-` prefix and accepts `agentic-operations`.
  - `postgres` and `kafka` are independent booleans, and both are passed to the skeleton and to GitOps generation.
  - The steps are: generate → ensure repository → GitOps onboarding config → catalog submit → **provision and merge GitOps onboarding** → platform sync → build.
- Earlier runs (#16 D-001) had the user onboard through Developer Hub. The service was in namespace `<name>-dev`, with an Argo app in `box1-workloads-dev/applications/`.

## Kafka

- `box1-ops-contracts/TOPICS.md` (`bb381b0`):
  - Five event topics and five DLQs.
  - Consumer group `ai-operations` is reserved on `box1.telemetry.events.v1` only.
  - The DLQs list "none; operator replay only", except the notification DLQ, which has `notification-replay`.
  - "Every topic needs a bounded retry path and auditable dead-letter/replay procedure."
- Live (`oc get kafkatopic -n box1-kafka`):
  - 10 topics are all Ready. One has 6 partitions and the rest have 3.
  - The Kafka listener is a single `plain`, port 9092, `tls: false`, with no authentication.
  - `oc get kafkauser -A` returns none (#71).

## Model inference (vLLM)

- `vllm/vllm-openai:v0.28.0`, Deployment `vllm-test` in namespace `vllm`, 15 days old, 1/1.
  - It has no Argo tracking annotation and is recorded as a manual install.
  - Args: `--served-model-name box1-coder`, `--model nvidia/Qwen3.8-27B-NVFP4`, `--max-model-len 98304`, `--max-num-seqs 1`, `--gpu-memory-utilization 0.85`, `--kv-cache-dtype fp8`, `--max-num-batched-tokens 8192`, `--enable-prefix-caching`, `--enable-auto-tool-choice --tool-call-parser qwen3_xml`, `--reasoning-parser qwen3`.
  - Resources: `limits nvidia.com/gpu: 1` only. There are no CPU or memory requests.
- Services:
  - `vllm-test-2` exposes 8000→8000.
  - `vllm-frontend` exposes 80→**9376**, a port the container does not listen on.
- Route `route-purple-bass`: `route-purple-bass-vllm.apps.ocp.box1.org` → `vllm-test-2:8000`, edge/Redirect.
- There is no NetworkPolicy in `vllm` and no `--api-key`.
- `GET /v1/models` through the API-server service proxy (authenticated as `mike`) returns `box1-coder`, max_model_len 98304, root `nvidia/Qwen3.8-27B-NVFP4`.
- **Security finding:** `GET https://route-purple-bass-vllm.apps.ocp.box1.org/v1/models` with **no credentials returned HTTP 200**. The inference endpoint accepts anonymous requests through the public route. Whether the host can be reached from outside the lab network was not tested. This belongs to #26; this run does not change it.

## Node capacity (single node `quark.host.box1.org`)

- Allocatable is 31.5 CPU, about 125 GiB memory and 1 GPU.
- Requests: CPU 23.3 (73%), memory about 87.8 GiB (70%). The GPU is 1/1, used by vLLM.
- Usage (`oc adm top`): 4.8 CPU, about 80.5 GiB (64%).
- The service needs no GPU. A small JVM request (100m / 384Mi) fits.

## MCP extension (quarkiverse/quarkus-mcp-server)

| Release | Date | Built against Quarkus |
|---|---|---|
| 2.0.4 (stable) | 2026-10-26 | `3.33.3.1` |
| 2.1.0.Beta1 (pre-release) | 2026-10-21 | `3.40.1` |

- Box1 services use Quarkus `3.40.1.1`. Whether 2.0.4 works on 3.40.1.1 is **not established**; it is checked by building in phase 3.
- `quarkus-mcp-server-oidc` (guide `guides-oidc.adoc`):
  - Uses standard `quarkus.http.auth.permission` on `/mcp/*` with `quarkus-oidc`.
  - Adds RFC 9728 protected-resource metadata and `insufficient_scope` 403 responses.
- Filters (`guides-using-filters-and-checks.adoc`):
  - `ToolFilter` controls visibility only.
  - **"If a filter throws an exception, it's ignored and the next filter executes"**, so a filter fails open. Authorization must be enforced in the tool or service method, not only in a filter.
- No box1-org repository uses MCP or LangChain4j.

## Evidence sources

| Source | Endpoint | Auth (box1-workloads-dev `932b1ba`) | v1 class |
|---|---|---|---|
| Order and timeline | order-service `GET /api/v1/orders/{id}`, `/timeline` | none (#40) | available |
| Fulfillment status | fulfillment-adapter `GET /api/fulfillments/{fulfillmentRequestId}` | `FULFILLMENT_READ_POLICY` set in Deployment (dev: permit) | available. The order API lacks `fulfillmentRequestId` (#78); take it from `fulfillment.requested.v1` in the Kafka window |
| Inventory and reservations | inventory-service `GET /api/v1/inventory`, `/reservations/{id}` | `INVENTORY_READ_POLICY` (dev: permit) | available |
| Telemetry alerts | asset-service `GET /api/v1/alerts` | bearer, role `telemetry-reader`, azp must be in `ASSET_READ_CLIENTS` | needs approval: Keycloak client, plus a config change in asset-service's workload |
| Notifications | notification-service `/api/v1/*` | `notification-reader` plus a console-client azp check | not used in v1; outcomes come from Kafka `notification.*` events |
| Deployed revision | each service's `/api/info` `gitRef` | anonymous | available |
| Argo CD revision | `applications.argoproj.io` status | OpenShift RBAC | unavailable in v1 (no RBAC for the service) |
| Traces | Tempo gateway, tenant `dev` | ClusterRole `box1-traces-read-dev` | needs approval (GitOps RBAC) |
| Metrics and alerts | thanos-querier and Alertmanager | ServiceAccount RBAC | needs approval (GitOps RBAC) |
| Logs | none | — | unavailable (#82) |
| Runbooks | box1-docs `runbooks/` | public repo | static versioned references only; RAG deferred |

## Identity

- Keycloak client CRs are in `box1-gitops/platform/identity/keycloak/realm/`: asset-service, developer-hub, fulfillment-adapter, inventory-service, notification-service, openshell, operations-console, scenario-controller-cli, scenario-controller.
- The `scenario-controller-client.yaml` pattern:
  - a confidential client with a service account and `fullScopeAllowed: false`;
  - the `roles` default scope, which is needed for `resource_access`;
  - an audience mapper;
  - `scopeMappings.clientMappings`, pinned to the target client's internal ID;
  - `serviceAccountClientRoles`;
  - caller-facing client roles;
  - a pinned `client.id`.
- People's tokens come from a separate `scenario-controller-cli` client.

## Console incidents (operations-console `9a87948`)

- `Incidents.java` derives incidents from order state; the console stores no incidents.
  - The ID is `inc_` + `orderId`.
  - Types are `ORDER_EXCEPTION` and `AWAITING_ERP_TOO_LONG`.
  - The threshold is `console.stuck-threshold`, default `10m`.
