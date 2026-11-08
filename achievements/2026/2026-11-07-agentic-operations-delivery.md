# agentic-operations: evidence-grounded incident analysis over REST and MCP, delivered and live

**Date:** 2026-11-06 to 2026-11-07 (America/New_York)

**Status:** Delivered and live in `agentic-operations-dev`. Acceptance is partial. [box1-docs#20](https://github.com/box1-org/box1-docs/issues/20) stays open: 3 of 8 boxes are ticked with cluster proof, and an [issue comment](https://github.com/box1-org/box1-docs/issues/20#issuecomment-6702512446) states every criterion's proof level. The live seeded-ERP-slowdown check was **waived by the user**. The other four criteria are proven in tests and CI but not on the cluster.

This was a `frontier` profile run. Its run state is in [`agent-runs/20-agentic-operations/`](../../agent-runs/20-agentic-operations/): decisions D-001 to D-015, the ledger, ten evidence files, six review-findings files and the handoff.

## Outcome

`agentic-operations` answers one question for operators: *what does the evidence say about this incident?*

- **Input:** a console incident ID (`inc_<orderId>`).
- **Evidence:** the service gathers a fixed, bounded set of read-only evidence for that one order. It asks the local model (vLLM `box1-coder`) for a structured analysis.
- **Output:** findings that must each cite evidence that exists, plus what could not be read, plus suggested actions that are **never executed**.
- **Interfaces:** the same capability is exposed over REST and as **MCP tools** through the Quarkiverse `quarkus-mcp-server` extension, so an MCP client such as an IDE agent can use it directly.

| Item | Value |
|---|---|
| Source | `box1-org/agentic-operations` `9d2d3e3` ([#1](https://github.com/box1-org/agentic-operations/pull/1)) |
| Image | `image-registry.openshift-image-registry.svc:5000/box1-ci/agentic-operations@sha256:21da40d46d29f4ed36f8bcc6e6453e1ba4627708837b5b4021666b01032e4818` |
| Build | `box1-ci/agentic-operations-release-2z4s4`. Build, security, promote and smoke all Succeeded. The run itself is marked `CouldntGetPipelineResult` (see Validation) |
| GitOps | `box1-workloads-dev` `55ed116` (promotion [#154](https://github.com/box1-org/box1-workloads-dev/pull/154)); Argo `agentic-operations` Synced/Healthy |
| Route | `https://agentic-operations-dev.apps.ocp.box1.org` (REST under `/api/v1/ai`, MCP at `/mcp`) |
| Model | In-cluster `http://vllm-test-2.vllm.svc:8000/v1`, served model `box1-coder` (`nvidia/Qwen3.8-27B-NVFP4`) |

**What the service does:**
- **REST.** `POST /api/v1/ai/incidents/{incidentId}/analyze` returns 202 with an `analysisId`. `GET /api/v1/ai/analyses/{analysisId}` returns the status, summary, cited findings, unknowns, evidence and proposed actions.
- **MCP** (Streamable HTTP, tools only). It has eight tools:
  - Read-only evidence: `get_order_timeline`, `get_fulfillment_status`, `get_inventory_reservation`, `list_recent_events`, `list_telemetry_alerts` and `get_deployed_revision`.
  - Analysis: `analyze_incident` and `get_analysis`.

  Every result is labelled `untrusted`. REST and MCP call one service layer, with one authorization point and one audit path.
- **Evidence:**
  - **Sources:** the order and its timeline, fulfillment status (located through the event window, since the order API lacks the ID, [#78](https://github.com/box1-org/box1-docs/issues/78)), the reservation, deployed revisions, the trace ID as a reference, and recent Kafka events.
  - **Entries:** each carries a ref, source, timestamps, a retrieval status and a trusted link.
  - **Unavailable sources:** telemetry alerts, trace contents, metrics and logs are listed as `UNAVAILABLE`, not silently omitted.
  - **Scope:** every read is for the requested order only, uses validated IDs, has one overall deadline and is size-capped.
- **The model gets no tools.**
  - The service, not the model, decides what is read.
  - Evidence goes only in the user message, framed as untrusted.
  - Guided JSON output is validated again on the server: findings without a valid citation are dropped, and actions outside an allowlist are dropped.
  - Downtime gives `MODEL_UNAVAILABLE`, and invalid or truncated output gives `MODEL_INVALID_OUTPUT`. Neither shows a diagnosis.
- **Kafka evidence window.**
  - It reads the five `box1.*.events.v1` topics as group `agentic-operations` and keeps a bounded window: 6 hours, 20,000 events, contract fields only.
  - It never commits, produces or writes a DLQ, and it is not part of readiness.
  - On startup it seeks to now minus 6 hours, so it refills after a restart.
- **State is in memory by the user's decision** (no PostgreSQL pod):
  - analyses are kept for 24 hours, 200 at most, and are lost on restart;
  - one replica, with the `Recreate` strategy;
  - one model call at a time (matching vLLM `--max-num-seqs 1`), a queue of 4, then 429.

**User decisions** (2026-11-06):
- service name `agentic-operations`, with no database and a Kafka consumer;
- MCP exposes both the evidence tools and the analysis tools;
- in-memory analysis state rather than another PostgreSQL pod;
- the Kafka window is evidence only, with no auto-triggered analyses;
- the RAG runbook index and the approval state machine are deferred, with durable state in [#97](https://github.com/box1-org/box1-docs/issues/97);
- v1 is operator-only, using the in-cluster vLLM.

## Starting baseline

- **Prompt.** [Service 10](../../box1_operations_agent_prompts/01-services/10_ai_operations.md) had no frontier profile. It proposed a repository `box1-ops-ai`, which the Golden Path template's name rule rejects.
- **Repository and GitOps.** Neither existed.
- **Contracts.** Group `ai-operations` was reserved on the telemetry topic only.
- **Keycloak.** No clients existed.
- **MCP.** Nothing in box1-org used MCP or LangChain4j.
- **vLLM.** A manual, non-GitOps deployment `vllm-test` serving `box1-coder` with 98,304 tokens and 1 sequence. **Its public Route answered an anonymous `GET /v1/models` with 200.**
- **Evidence access.** The order API has no authentication ([#40](https://github.com/box1-org/box1-docs/issues/40)). Fulfillment and inventory reads are permitted in dev. Telemetry, Tempo and Thanos need grants that no service had. There is no centralized logging ([#82](https://github.com/box1-org/box1-docs/issues/82)).
- **Node.** 73% of CPU and 70% of memory were already requested, and the GPU was fully allocated to vLLM.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Prompt | [box1-docs#96](https://github.com/box1-org/box1-docs/pull/96) | `12f0b11` | Frontier profile for Service 10 with the user's decisions (name, no database, Kafka, MCP, in-memory state, deferrals). Manifest 1.8. Issue #20 mirrored |
| Onboarding | [box1-workloads-dev#146](https://github.com/box1-org/box1-workloads-dev/pull/146), [#147](https://github.com/box1-org/box1-workloads-dev/pull/147) | `fe383c6` (#146) | The user onboarded the service in Developer Hub (`quarkus-rest-service`, Kafka on, PostgreSQL off) |
| Contracts | [box1-ops-contracts#13](https://github.com/box1-org/box1-ops-contracts/pull/13) | `7b7fbac` | `ai-operations` renamed to `agentic-operations` and added to all five event topics, with a "read-only consumer groups" section |
| Identity | [box1-gitops#99](https://github.com/box1-org/box1-gitops/pull/99) | `26482b8` | Bearer-only client `agentic-operations` (roles `aiops-viewer` and `aiops-analyst`, preset internal ID) and public PKCE/device client `agentic-operations-cli` (audience mapper and role scope mapping) |
| Runtime | [box1-workloads-dev#153](https://github.com/box1-org/box1-workloads-dev/pull/153) | `bee7db7` | `Recreate`; explicit Deployment `env` (OTel, OIDC issuer, accepted `azp`, consumer group, in-cluster vLLM, upstream URLs); ServiceMonitor; PrometheusRule (`Box1ServiceDown`, `AiopsModelUnavailable`, `AiopsWindowSeekFailed`, `AiopsKafkaRecordsSkipped`) |
| Service | [agentic-operations#1](https://github.com/box1-org/agentic-operations/pull/1) | `9d2d3e3` | Service, 69 tests, evaluation dataset, `docs/index.md` (API, MCP catalog, security boundaries, configuration, runbook) |
| Promotion | [box1-workloads-dev#154](https://github.com/box1-org/box1-workloads-dev/pull/154) | `55ed116` | Digest `21da40d4…`, merged by the pipeline |
| Run state | [box1-docs#103](https://github.com/box1-org/box1-docs/pull/103) | `989d6d0` | `agent-runs/20-agentic-operations/` merged to `main` |

The user approved each merge. They were merged in the order contracts, Keycloak, runtime, service, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)), so the service never started without its prerequisites.

**Decisions with consequences** (records are in the run state's `decisions/`):
- **MCP version (Q-2).** Stable `quarkus-mcp-server` 2.0.4 is built against Quarkus 3.33. It passed a Streamable HTTP protocol test and the full suite on Quarkus 3.40.1.1, so the beta was not needed. It is **tested, not declared compatible**.
- **Authorization lives in the service layer (D-004).** MCP tool filters are ignored when they throw, so they fail open and are never the enforcement point. On top of the service-layer check, the HTTP layer requires an `aiops-*` role.
- **No model tools (D-006, D-010).** Prompt injection cannot cause a tool call, because there is no tool loop. The most it can do is mislead a summary, which the citation checks and the evaluation measure.
- **Incident alignment (D-002, amended in review).** The service uses the same rules as the console's `Incidents.current()`. An order awaiting the ERP is an active `AWAITING_ERP_TOO_LONG` incident even below the 10-minute threshold.

## Validation and evidence

| Test | Expected | Observed |
|---|---|---|
| Local suite (`./mvnw verify`, `0cf2604`) | Pass | 69 tests, 0 failures, 0 Checkstyle violations. They cover: the REST and MCP authorization matrix, parity, invalid IDs and unknown tools with no upstream reads, model down/timeout/invalid/truncated/tool-call, uncited findings dropped, queue bound, store expiry, window dedupe/poison/bounds/correlation/time pruning, seek failure, stalled and oversize bodies |
| Evaluation dataset: 7 cases through REST and MCP, deterministic model | Expectations met | 7/7. The cases: slow ERP, inventory denial, broker outage, healthy control, missing evidence, conflicting evidence, prompt injection. Citation coverage 1.0, 0 role leaks, 0 upstream reads caused by injection, 0 tool errors, p95 18 ms. This scores the pipeline, not model quality |
| PR CI (`agentic-operations-validate-6lt27`) | Pass | 69 tests plus 5 ITs |
| Production-profile jar, locally, with Kafka and the model unreachable | Starts, ready, denies anonymous calls | Readiness 200; anonymous and forged-token calls get 401 on REST and `/mcp`; 0 token strings and 0 ERROR lines in the log |
| Live model probe against `box1-coder` | Valid guided JSON | Healthy order: valid, no invented fault, `NO_ACTION`, 1,321 prompt tokens, 2.8 s. Injected `statusReason`: flagged as an injection and not followed. One sample each |
| Release (`agentic-operations-release-2z4s4`) | Succeeded | All four tasks Succeeded, but the run is marked `CouldntGetPipelineResult`: the pipeline declares `SCAN_OUTPUT`, which the security task does not emit while gates are disabled. **The image was released without ACS or TPA checks**, under the template default ([#42](https://github.com/box1-org/box1-docs/issues/42)) |
| Running image | Promoted digest | GitOps digest = pod `imageID` = `sha256:21da40d4…`; Deployment annotation and `/api/info` `gitRef` = `9d2d3e3` |
| Keycloak after #99 | Clients and roles correct | Both clients `ready`, no operator errors. A device-grant login (approved in the user's browser as `mike`; the run never handled a password) gave a token with `aud=agentic-operations`, `azp=agentic-operations-cli`, and only `aiops-analyst` and `aiops-viewer`. This shows the preset-ID scope mapping works |
| Anonymous or forged token, live | 401 | 401 on analyze, get and MCP `initialize` |
| Live REST analysis of a real shipped order | Cited evidence, no invented fault | COMPLETED in 4.2 s. 9 sources OK (fulfillment included), 4 stated `UNAVAILABLE`. "No faults or errors are indicated", `NO_ACTION`, 4,718 and 222 tokens |
| Live MCP session | Catalog, labelling, rejection, parity | Exactly 8 tools; `untrusted: true`; a URL as an order ID gives a tool error with no upstream read; MCP analysis evidence identical to REST |
| Tracing (Tempo) | One trace across services | REST: `POST …/analyze`, then `aiops.analysis`, then spans in order-service, inventory-service and fulfillment-adapter. **MCP requests have no server span** |
| Live Kafka window | Refills from the broker | 18 partitions sought to now minus 6 h about 4 s after start; 144 events; 0 skipped |
| Logs | No secrets or evidence | Audit lines hold only the tool, ID (or `invalid`), subject, decision, duration and size |

**Review.** Five same-model reviewer passes (architecture, messaging, security, operations, release; persistence not applicable) found **no high-severity defects**. They found **11 distinct medium** ones, counting duplicates across passes once, that the passing tests had missed. Every finding in the service code was fixed except one low one that was accepted (O(n) eviction at lab volumes). The suite and CI were rerun, and the remaining findings went into the platform PRs. The most important:
- an upstream that stalled mid-body could hold the only analysis worker indefinitely, after which every call got 429;
- Kafka payloads kept every small field, so the window had no real memory bound;
- an uncited model summary was shown as the answer when every finding had been dropped;
- a BUSY rejection evicted a stored analysis;
- worker threads lost the trace context.

**Two defects were found only by running against real systems:**
- **The JDK HTTP client's HTTP/2 cleartext upgrade made vLLM answer 400 to every request.** Both clients are now pinned to HTTP/1.1, with a regression test.
- **Quarkus OIDC logged raw bearer tokens at WARN** when verification failed, then fell back to remote introspection. The logger is now set to ERROR and introspection is off.

**Not tested on the cluster:**
- **The seeded ERP slowdown**, waived by the user. `erp-delayed-processing` needs ERP demo faults, which are off in the cluster image ([#83](https://github.com/box1-org/box1-docs/issues/83)), and a person at the ERP console. The manual-hold alternative was declined.
- A viewer-only 403. The live account holds both roles; CI proves it.
- Model downtime.
- A pod restart.
- Poison and duplicate Kafka records.
- Prometheus scraping. Thanos was not reachable with this session.
- Rollback.

## Final operational state

- **Argo `agentic-operations`** (automated, selfHeal) manages the service from `box1-workloads-dev` `55ed116`, at digest `21da40d4…`. It runs one replica with `Recreate` and 11 explicit env settings. The ServiceMonitor and PrometheusRule exist.
- **Keycloak** has clients `agentic-operations` and `agentic-operations-cli`, managed by Argo from `box1-gitops`. Role assignment is manual, and the user holds both roles. The operator also created Secret `keycloak-client-secret-agentic-operations` in `keycloak`, which nothing uses.
- **Kafka:** group `agentic-operations` is declared in `TOPICS.md`. It holds no committed offsets.
- **vLLM** is unchanged: still a manual deployment, and its public Route still accepts anonymous requests. The service uses only the in-cluster Service.
- **Data left on the cluster:** none. No orders were created. Two analyses of `ord_2f6bb653…` are held in memory until they expire.
- **Idle resource use:** 8m CPU and 185Mi memory (512Mi limit).

## Recovery and follow-ups

- **Roll back** by reverting promotion #154 in `box1-workloads-dev`. The service holds no state. To remove it, revert #153, then #99 for the clients and #13 for the group declaration. Rollback has not been exercised.
- **Operator procedures** are in `docs/index.md` in agentic-operations: statuses, metrics, model down, BUSY, window refill, shutdown, tracing, rollback.
- **Open on #20:** five criteria without cluster proof, one of them waived. The issue comment gives each proof level.
- **Follow-ups:**
  - **The `SCAN_OUTPUT` false failure:** [box1-gitops#104](https://github.com/box1-org/box1-gitops/pull/104) is open (`box1-security-gates` always emits `SCAN_OUTPUT`), with a comment on #42. Not merged.
  - **The anonymous public vLLM Route:** to raise on [#26](https://github.com/box1-org/box1-docs/issues/26). A session has been proposed but not started.
  - **Durable analysis and approval state:** [#97](https://github.com/box1-org/box1-docs/issues/97).
  - **Not filed yet:**
    - a server span for MCP requests;
    - per-service checks in the release smoke task (it checks only template endpoints);
    - a telemetry read grant on asset-service;
    - Tempo and Thanos RBAC (Q-6);
    - the console "Analyze" button ([#18](https://github.com/box1-org/box1-docs/issues/18)).
