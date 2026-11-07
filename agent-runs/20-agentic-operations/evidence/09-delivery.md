# Phase 6: delivery

The user approved the merges ("Yes, merge in order", 2026-11-06). They were merged about 10 seconds apart (box1-docs#64):

| Order | PR | Merge commit | Time (UTC) |
|---|---|---|---|
| 1 | box1-ops-contracts#13 (merge commit) | `7b7fbac` | 2026-11-07T04:20:39Z |
| 2 | box1-gitops#99 (squash) | `26482b8` | 04:20:53Z |
| 3 | box1-workloads-dev#153 (squash) | `bee7db7` | 04:26:39Z |
| 4 | agentic-operations#1 (squash) | `9d2d3e3012388e7c94e42fbc492d9fcc5bb15041` | 04:26:53Z |

## Keycloak (after #99)

- KeycloakClients `agentic-operations` and `agentic-operations-cli` in namespace `keycloak` are both `ready=true`. The operator logged no errors, failures or 404s in the 15 minutes after the sync, so the preset-ID scope mapping did not 404 as it did in afb99c4.
- `POST /auth/realms/box1/protocol/openid-connect/auth/device` with `client_id=agentic-operations-cli` returned `invalid_request: Missing parameter: code_challenge_method`, so the client exists and PKCE is enforced. An unknown client returns `invalid_client`.
- **Not verified:**
  - that the roles `aiops-viewer` and `aiops-analyst` exist;
  - that the CLI scope mapping took effect;
  - the token claims (`aud`, `azp`, `resource_access.agentic-operations.roles`).

  These need a user with an assigned role to sign in, and assigning roles is the user's step.

## Runtime settings (#153)

Argo `agentic-operations` is Synced/Healthy. The Deployment has `strategy=Recreate`, `replicas=1` and the 11 env settings. ServiceMonitor `agentic-operations` and PrometheusRule `agentic-operations-availability` exist. **Prometheus scraping is not verified:** the Thanos querier could not be reached through the API-server proxy with this session.

## Release and promotion (#1)

- **Release PipelineRun:** `agentic-operations-release-2z4s4`.
  - Tasks: `build` (digest `sha256:21da40d4…`), `security` (all `disabled`), `promote` (box1-workloads-dev#154, `55ed116`, `promoted=true`) and `smoke` all **Succeeded**.
  - **The PipelineRun itself is marked failed: `CouldntGetPipelineResult`, "invalid pipelineresults [SCAN_OUTPUT], the referenced results don't exist".**
  - Cause: the template's `.tekton/release.yaml` declares the pipeline result `SCAN_OUTPUT` from `tasks.security.results.SCAN_OUTPUT`, but the security task emits no `SCAN_OUTPUT` when `security-gates` is `disabled`.
  - The same result appears on three notification-service releases (`mpbtb`, `6x952`, `v4q5h`). operations-console and fulfillment-adapter run their security gates and succeed. This relates to box1-docs#42 (security gates disabled by default), which does not record this symptom. It has not been raised there.
- **Security:** this image was released **with no ACS or TPA check**, because of the template default (#42).
- **Promotion:** box1-workloads-dev#154 "Promote agentic-operations 9d2d3e301238 to development" was auto-merged as `55ed116`.

| Check | Result |
|---|---|
| GitOps digest (`kustomization.yaml`) | `sha256:21da40d46d29f4ed36f8bcc6e6453e1ba4627708837b5b4021666b01032e4818` |
| Running pod imageID | the same digest |
| Deployment `box1.org/source-revision` | `9d2d3e3012388e7c94e42fbc492d9fcc5bb15041` |
| `GET /api/info` `gitRef` | `9d2d3e3012388e7c94e42fbc492d9fcc5bb15041` |
| Argo | Synced/Healthy at `55ed116` |

## Live checks (public route `agentic-operations-dev.apps.ocp.box1.org`)

| Check | Result |
|---|---|
| `/q/health/ready` | 200 |
| Anonymous `POST /api/v1/ai/incidents/inc_ord_x/analyze` | 401 |
| Anonymous `GET /api/v1/ai/analyses/{id}` | 401 |
| Anonymous MCP `initialize` on `/mcp` | 401 |
| Forged bearer token | 401 |
| `/q/openapi` paths under `/ai/` | `/api/v1/ai/analyses/{analysisId}` and `/api/v1/ai/incidents/{incidentId}/analyze` |

## Live Kafka window (real broker)

- **Startup:** started at 04:29:51Z. At 04:29:55Z the log reads `window start: 18 partitions positioned at <now−6h>` (five topics: 4×3 partitions plus 6 for telemetry). There were no seek failures.
- **Window contents:** `aiops_window_events 144` and `aiops_window_oldest_age_seconds 21344` (about 5.9h).
- **Records accepted** (`aiops_kafka_records_total{outcome="accepted"}`): order 89, inventory 19, fulfillment 17, notification 19. There were no skipped records.
- **Resource use:** `oc adm top pod` showed 8m CPU and 185Mi memory, against a 256Mi request and 512Mi limit.
- **Refill time** after start is under about 4 seconds. That covers the seek; record ingestion was complete by the time of the metric read.
