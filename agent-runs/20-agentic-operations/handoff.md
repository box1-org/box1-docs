# Agent handoff — box1-docs#20 agentic-operations (frontier)

## Work completed
- **Service / platform workstream:** Service 10, AI Operations, delivered as `agentic-operations`. It analyzes incidents from cited evidence over REST and MCP. Read and propose only.
- **Slice / requirements:** the whole vertical slice through phase 7, except the live seeded ERP slowdown, which the user waived.
- **Requirements deferred by user decision (`superseded`):**
  - the RAG runbook index;
  - the approval state machine. Durable state is tracked in #97.
- **Repository and branch:** box1-org/agentic-operations, merged to `main` as `9d2d3e3` (PR #1, branch `issue-20-agentic-operations`).
- **Changed paths:**
  - `pom.xml`: quarkus-mcp-server-http and -oidc 2.0.4, quarkus-oidc, logging-json, opentelemetry, plus test dependencies;
  - `src/main/java/org/box1/aiops/**`: config, Ids, BoundedHttp, security, evidence, window, model, analysis, api, mcp;
  - `src/main/resources/application.properties`;
  - `src/test/java/org/box1/aiops/**` and `src/test/resources/eval/cases.json`;
  - `docs/index.md` and `README.md`.
- **PRs, all merged with the user's approval:**

| PR | Merge commit | Content |
|---|---|---|
| box1-docs#96 | `12f0b11` | Frontier profile for the prompt |
| box1-ops-contracts#13 | `7b7fbac` | Consumer group |
| box1-gitops#99 | `26482b8` | Keycloak clients |
| box1-workloads-dev#153 | `bee7db7` | Runtime |
| agentic-operations#1 | `9d2d3e3` | Service |
| box1-workloads-dev#154 | `55ed116` | Promotion |

## Tests and deployment proof
- **Commands and results:**
  - `./mvnw -B -ntp verify` on `0cf2604`: 69 tests, 0 failures, 0 Checkstyle violations.
  - The evaluation dataset (7 cases, REST and MCP, deterministic model): 7/7 expectations met, citation coverage 1.0, 0 role leaks, 0 injection-driven reads, 0 tool errors, p95 18 ms. See `evidence/04`.
  - Live probes against `box1-coder`: a healthy control, and an injection that was flagged and not followed (`evidence/05`). These probes found the h2c-upgrade 400 bug.
  - Production-profile jar runs (`evidence/05`, `07`).
- **CI:**
  - `agentic-operations-validate-6lt27` Succeeded on `0cf2604` (69 tests and 5 ITs).
  - Release `agentic-operations-release-2z4s4`: build, security, promote and smoke all Succeeded. **The PipelineRun is marked `CouldntGetPipelineResult`**, because `SCAN_OUTPUT` is missing when the template disables security gates. The same happens to notification-service (`evidence/09`).
- **GitOps PR and deployed digest:**
  - Promotion box1-workloads-dev#154 (`55ed116`). Digest `sha256:21da40d46d29f4ed36f8bcc6e6453e1ba4627708837b5b4021666b01032e4818`, the same in GitOps and the pod's imageID.
  - Deployment annotation and `/api/info` `gitRef` are both `9d2d3e3`. Argo is Synced/Healthy.
- **Endpoints verified live (`evidence/09`, `10`):**
  - Anonymous calls and forged tokens get 401 on `/api/v1/ai/*` and `/mcp`.
  - A device-grant token for `mike` carries the correct `aud`, `azp` and roles.
  - REST analysis of real order `ord_2f6bb653…`: COMPLETED in 4.2s with 9 sources OK and 4 stated UNAVAILABLE. Healthy result with no invented fault, `NO_ACTION` only.
  - MCP: catalog of 8 tools, untrusted labelling, invalid argument rejected, and analysis evidence identical to REST.
  - A Tempo trace spans 4 services.
  - The Kafka window filled from the live broker: 18 partitions, 144 events.

## Contract state
- **OpenAPI / event schemas changed:**
  - Service OpenAPI: `POST /api/v1/ai/incidents/{incidentId}/analyze` and `GET /api/v1/ai/analyses/{analysisId}`.
  - MCP catalog in `docs/index.md`.
  - No event schemas changed.
  - `TOPICS.md` declares the read-only group `agentic-operations` on the five event topics (box1-ops-contracts#13).
- **Database migrations:** none; the service has no database (D-003).
- **Consumer compatibility / pending follow-up:**
  - The group never commits offsets, so it does not affect other groups.
  - The window keeps only contract fields; new payload fields are ignored until `EvidenceWindow.KEPT` is updated.

## Operations and safety
- **Secrets and auth boundaries:**
  - No secrets in the service. Keycloak `agentic-operations` is bearer-only and owns `aiops-viewer` and `aiops-analyst`; `agentic-operations-cli` is public (PKCE or device grant).
  - The HTTP layer requires an `aiops-*` role. `Guard` re-checks roles and `azp=agentic-operations-cli` in the service layer.
  - Introspection is off, and the OIDC logger that prints tokens is quieted.
  - The model gets no tools. Evidence is untrusted and allowlisted, and actions are never executed.
- **Telemetry evidence:**
  - The `aiops_*` metrics are live.
  - ServiceMonitor and PrometheusRule `agentic-operations-availability` exist (4 alerts). **Scraping is not verified.**
  - Traces are linked across services for REST. **MCP requests have no server span.**
- **Resource settings:** requests 100m/256Mi, limits 1 CPU/512Mi; observed 185Mi. One replica, `Recreate`.
- **Known risks:**
  - **The image shipped without ACS or TPA checks**, under the template default (#42).
  - The vLLM public route accepts anonymous requests (#26, not raised).
  - Kafka has no authentication (#71).
  - Analyses are lost on restart, by design (#97).
- **Recovery / rollback:**
  - Promote the previous digest through box1-workloads-dev.
  - Revert box1-workloads-dev#153 for the runtime settings, and box1-gitops#99 to remove the clients.
  - The service holds no state.

## Next agent session
- **Next smallest slice:** none required for #20. Optional follow-ups for the user to decide:
  - a live viewer-only 403 and a pod-restart check;
  - a server span for MCP requests;
  - per-service release smoke checks;
  - the `SCAN_OUTPUT` false failure (#42);
  - the vLLM public route (#26);
  - the console Analyze button (#18);
  - an asset-service read grant for telemetry alerts (Q-5);
  - Tempo and Thanos RBAC (Q-6).
- **Files to read:** `checkpoint.md`, `requirements.yaml`, `evidence/09-delivery.md`, `evidence/10-live-acceptance.md`, and `docs/index.md` in agentic-operations.
- **Blockers and user decisions:** Q-6 (deferred RBAC); whether to enable ERP demo faults (#83 item 2).
- **Context budget warning:** not applicable (`frontier`).

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#20
current_phase: "7 complete except the waived ERP scenario"
repositories:
  - name: box1-org/agentic-operations
    branch: main
    commit: 9d2d3e3012388e7c94e42fbc492d9fcc5bb15041
  - name: box1-org/box1-docs
    branch: agent-run/20-agentic-operations
    commit: (this commit)
  - name: box1-org/box1-ops-contracts
    branch: main
    commit: 7b7fbac
  - name: box1-org/box1-gitops
    branch: main
    commit: 26482b8
  - name: box1-org/box1-workloads-dev
    branch: main
    commit: 55ed116
run_state_path: agent-runs/20-agentic-operations/
requirements:
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 9
  live_verified: 5
  blocked: 0
  superseded: 2
image_digest: sha256:21da40d46d29f4ed36f8bcc6e6453e1ba4627708837b5b4021666b01032e4818
gitops_commit: box1-workloads-dev 55ed116 (promotion #154)
review_passes_completed: [architecture, messaging, security, operations, release, persistence (n/a)]
open_decisions: [Q-6 trace/metrics RBAC deferred, ERP demo faults (#83)]
rollback_state: "previous digest sha256:eb145100… (template scaffold 61bcb8c); not exercised"
next_action: "None required for #20. Offer the follow-ups listed above, then the achievement log when the user asks."
```
