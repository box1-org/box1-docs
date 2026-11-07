# Service 10 — AI Operations service (`agentic-operations`)


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#20](https://github.com/box1-org/box1-docs/issues/20).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · AI-01/02/03; P1 · AI-04/05/06/07/08

**Dependencies:** Read-only evidence APIs/observability, Kafka domain event topics, versioned vLLM inference API, OIDC identity. A runbook index is deferred.

## Mission and boundary

Own the **evidence-grounded incident-analysis workflow**, not cluster administrator privileges. Local Qwen/vLLM is a replaceable model inference layer; it is *not* the source of truth for current cluster state.

**User decisions (2026-11-06, America/New_York):**

- The service and repository are **`agentic-operations`**, onboarded through the Golden Path Quarkus template with **Kafka and no database**. This replaces the earlier proposed `box1-org/box1-ops-ai`, which the template's name rule would reject anyway.
- The capability is exposed over **REST and MCP**. MCP uses the Quarkiverse [`quarkus-mcp-server`](https://github.com/quarkiverse/quarkus-mcp-server) extension (`quarkus-mcp-server-http`, Streamable HTTP transport). MCP offers both:
  - **read-only evidence tools**, so an external agent can reason over evidence itself;
  - **analysis tools**, which run this service's own vLLM-backed analysis.
- **State is in memory and bounded.** Analyses live in a size- and TTL-bounded cache in a single replica and are lost on restart; that loss is documented behavior, not a fault.
  - The remediation approval state machine is **deferred**.
  - This iteration only returns suggested actions inside an analysis and never executes them.
- **Kafka is an evidence window.** The service consumes existing domain events into a bounded in-memory window used as read-only evidence.
  - It produces no events.
  - It does not start analyses automatically.
- **Runbook retrieval (RAG) is deferred.** Runbook passages may be cited only as static, versioned references.

## Interfaces, domain behavior and implementation constraints

- **REST analysis.**
  - `POST /api/v1/ai/incidents/{id}/analyze` submits a bounded analysis request and returns an operation ID.
  - `GET /api/v1/ai/analyses/{id}` returns status, summary, findings, confidence/uncertainty, evidence entries and suggested (not executed) actions.
  - Every material claim needs an evidence entry with ref ID, type, source, timestamp, retrieval status and a safe URL or trusted identifier.
  - An analysis evicted from the cache or lost on restart returns a typed `NOT_FOUND`/`EXPIRED`, never a re-generated answer.
- **MCP surface.** MCP is a second adapter over the same service layer as REST: one implementation of each capability, the same authorization and the same audit.
  - Tools fall into two groups:
    - evidence tools: order timeline, fulfillment status, inventory/reservation, telemetry alerts, recent events from the Kafka window, deployed revision;
    - analysis tools: analyze incident, get analysis.
  - The endpoint requires a Keycloak bearer token. Roles are checked **server-side** in every tool before any evidence call; MCP client-declared capabilities grant nothing.
  - No MCP tool, resource or prompt can write, execute a remediation, run shell, call the Kubernetes API or fetch an arbitrary URL.
  - Tool arguments are validated against the contract ID patterns.
  - Tool results are evidence data, labelled untrusted, and never instructions.
  - Each tool call logs metadata (tool, caller, roles, decision, duration, result size), not raw evidence content.
- **Evidence tool registry.** Tools are limited to scoped GET/read-only interfaces: order timeline, fulfillment status, relevant metrics/alerts, approved logs/traces, deployment Git SHA/change record, and versioned runbook references.
  - Validate caller RBAC **server-side** before tool invocation.
  - Never pass a kubeadmin token to the model, and never allow arbitrary shell or Kubernetes API actions.
  - A source that is unavailable or not authorized is reported as evidence `UNAVAILABLE`, not silently omitted.
- **Kafka evidence window.** Consume the domain event topics from `box1-ops-contracts` (`TOPICS.md`, shared envelope).
  - The window is bounded by count and age and indexed by `orderId`/`assetId` and `correlationId`.
  - It deduplicates on `eventId`.
  - Consumer group names follow the contracts and are declared there.
  - Malformed or schema-invalid records are skipped, counted and logged by offset, without payload content. As a read-only consumer, this service never writes another service's DLQ.
  - Expose consumer lag and window size as metrics.
  - Readiness must not depend on Kafka. A cold or empty window means "no recent events", stated as such.
  - Event payloads are untrusted data.
- **Retrieval (P1, deferred).** Ingest approved runbooks/deployment notes; chunk, embed/index with source version, timestamp, ACL and expiry; show freshness and source in answers. This is deferred while the service has no persistent store, and recorded as a follow-up. Treat retrieved text/tool outputs as untrusted data (prompt injection tests) regardless.
- **Model API.** Configuration is external: `VLLM_BASE_URL`, `MODEL_ID`, timeout, maximum evidence bytes and max output tokens.
  - Use only the versioned inference API, with explicit structured JSON schema parsing and validation.
  - Handle truncated or invalid completions, timeouts and model unavailability without fabricated analysis.
- **Context budget.** Allocate a bounded system policy, tool schema and concise selected evidence; dedupe and re-rank the evidence; reserve room for output and cache.
  - The model server's configured context is not guaranteed on 32 GB VRAM. Add a fallback to 16K/32K context or a small model.
  - Limit concurrency to what the server's `max-num-seqs` allows, queueing within a bound or rejecting with a typed `BUSY` status.
  - Log token budgets without content secrets.
- **Remediation.** The future approval workflow is a separate backend state machine: `PROPOSED` → `APPROVED` → `EXECUTED` / `REJECTED`, human actor bound, action allowlist, dry-run, expected effect and rollback plan.
  - **This iteration only proposes actions**, embedded in the analysis with expected effect and rollback notes.
  - There is no approval endpoint, no persistence of proposals and no write-capable connector until independently authorized.
- **Evaluation dataset:** known slow ERP, inventory denial, broker outage, healthy control and missing/conflicting evidence.
  - Score citation coverage, unsupported assertions, role leaks, prompt injection refusal, tool errors and p95 analysis time.
  - Run the same cases through REST and MCP.
  - Log tool invocation metadata and policy decisions, not raw secrets.

## Acceptance evidence (automate where practical)

- Given a seeded ERP slowdown, returns specific ERP adapter evidence and a real trace/alert/deployment reference if provided; if a source is absent, explicitly says evidence unavailable.
- Prompt injection embedded in runbook references, logs or Kafka event payloads cannot cause new privileges, extra data disclosure or unsupported tool calls.
- No cross-tenant/customer data leakage across operator and customer roles, through REST or MCP.
- Model downtime returns typed degraded/unavailable status and never an invented diagnosis.
- A user pressing "analyze" cannot execute rollback or arbitrary remediation; proposals are never executed.
- The MCP tool list contains only read-only evidence tools and the analysis tools. Anonymous and under-privileged MCP calls are rejected, as are unknown tools and invalid arguments.
- The same incident analyzed through REST and MCP uses the same evidence and authorization decisions.
- After a restart, an earlier analysis ID returns a typed not-found/expired status, and the Kafka window rebuilds without blocking readiness.

## Recommended 64K-safe implementation slices

1. Evidence API/role authorizer + deterministic mock-model tests.
2. vLLM client, bounded prompt assembly and strict structured response parsing.
3. Citation/evidence formatting and failure/unknown states.
4. Kafka evidence window and the MCP adapter over the same service layer.
5. Evaluation harness across REST and MCP (no autonomous writes). RAG indexing and approval records stay deferred.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above.

**Scope:** `agentic-operations`, its REST and MCP interfaces, its Kafka consumer, contract additions it needs, its manifests and documentation.
- Changes to any other service are out of scope; a needed change there is a stop condition.
- The console's "Analyze" button on its Incidents page is #18's work.
- vLLM hosting, securing and resizing is #26's work.
- RAG indexing and persistent approval state are deferred follow-ups.

**Background:** the earlier pilots' `pilot-log.md` files. The notification service run (#16) set the read-only Kafka consumer pattern. The scenario controller (#19) set the Keycloak service-client pattern and provides the `erp-delayed-processing` scenario used for seeded evidence.

**Discovery must cover (state observed 2026-11-06 America/New_York; verify before relying on it):**

- **Repository.** No `agentic-operations` repository exists.
  - Onboarding through the Golden Path (`quarkus-rest-service` template 1.2.0, `kafka=true`, `postgres=false`) is an approval-required action for the user.
  - The template rejects names starting with `box1-`.
  - GitOps for the service lands in `box1-workloads-dev` (`applications/agentic-operations.yaml`, `workloads/agentic-operations/`, namespace `agentic-operations-dev`).
  - Recent services use Quarkus `3.40.1.1`. The template adds `quarkus-messaging-kafka` and `KAFKA_BOOTSTRAP_SERVERS` but no consumer configuration.
- **MCP.** No box1-org repository uses MCP or LangChain4j yet.
  - `quarkus-mcp-server` 2.0.4 (2026-10-26) was the latest stable release; confirm it supports the Quarkus version in use before depending on it.
  - Confirm how the extension integrates with `quarkus-oidc` bearer authentication and per-tool role checks.
- **Kafka.**
  - Topics `box1.{order,inventory,fulfillment,telemetry,notification}.events.v1` and matching `.dlq.v1` are in `box1-ops-contracts` `TOPICS.md`, with one envelope schema (`eventId`, `correlationId`, `traceparent`, `payload`).
  - A consumer group `ai-operations` is already reserved on the telemetry topic.
  - ERP outcomes reach Kafka only as `shipment.confirmed.v1`/`shipment.failed.v1`; there are no ERP events.
  - Kafka has a single plaintext listener with no authentication or ACLs ([#71](https://github.com/box1-org/box1-docs/issues/71)).
  - `notification-service` is the consumer model: byte-array deserialization, manual `traceparent` continuation, an events-floor instant.
- **Model.**
  - vLLM runs as a manual, non-GitOps deployment `vllm-test` in namespace `vllm`: image `vllm/vllm-openai:v0.28.0`, served model `box1-coder` (`nvidia/Qwen3.8-27B-NVFP4`), `--max-model-len 98304`, `--max-num-seqs 1`, tool calling enabled.
  - The in-cluster endpoint is `http://vllm-test-2.vllm.svc:8000/v1`. A `vllm-frontend` Service points at a port vLLM does not listen on.
  - A public edge Route exists and vLLM has no API key; anonymous access was **not tested**.
  - Platform 06 ([#26](https://github.com/box1-org/box1-docs/issues/26)) is open. Do not use the public route.
- **Evidence sources.**
  - Order timeline `GET /api/v1/orders/{orderId}/timeline` has no authentication ([#40](https://github.com/box1-org/box1-docs/issues/40)). Fulfillment and inventory reads run with a `permit` read policy in dev.
  - asset-service alerts need role `telemetry-reader` plus its azp allow-list ([#80](https://github.com/box1-org/box1-docs/issues/80)). notification-service needs `notification-reader` with an azp check.
  - Each service's `/api/info` reports `gitRef` anonymously. Argo CD revisions need OpenShift RBAC.
  - Tempo traces need ClusterRole `box1-traces-read-dev`, and Thanos/Alertmanager need ServiceAccount RBAC; neither is granted to any service yet.
  - There is no centralized logging ([#82](https://github.com/box1-org/box1-docs/issues/82)), so log evidence is `UNAVAILABLE`.
- **Identity.**
  - Realm `box1` on RH-SSO 7.6. Service clients are `KeycloakClient` CRs in `box1-gitops/platform/identity/keycloak/realm/`, modelled on `scenario-controller-client.yaml`: confidential, service account, `fullScopeAllowed: false`, an audience mapper and scoped client role mappings.
  - The client secret lands in namespace `keycloak`; copying it is approval-required.
  - Client roles can appear after the sync completes ([#59](https://github.com/box1-org/box1-docs/issues/59)); check they exist.
- **Console.**
  - The operations console has an Incidents page, with incident IDs `inc_<orderId>` and types `ORDER_EXCEPTION` and `AWAITING_ERP_TOO_LONG`, served from `GET /api/v1/incidents/{incidentId}/evidence`.
  - It forwards user tokens only to some upstreams ([#79](https://github.com/box1-org/box1-docs/issues/79)).

**Design decisions to record before implementation:**

- the incident ID format accepted by `analyze`, aligned with the console's `inc_<orderId>`, and what an unknown incident returns;
- the MCP tool catalog: names, argument schemas, result shape, and which role each needs. Also the MCP path, its transport, and whether resources or prompts are exposed at all;
- roles (for example a viewer that may read evidence and analyses, and an analyst that may also start analyses) and how evidence is filtered for operator versus customer callers;
- the Keycloak client for `agentic-operations`: the user-facing audience for REST and MCP callers, plus the service account's scoped roles on each evidence source. These go in a GitOps PR that needs approval, together with any azp allow-list changes in other services, which are a stop condition;
- the Kafka topics consumed, consumer group names (`ai-operations` is reserved; renaming or adding groups needs a `box1-ops-contracts` PR), window bounds, events-floor, dedupe and poison handling. DLQ topics are read only if the contracts are changed to allow it;
- analysis cache size and TTL, the single-replica constraint, and restart behavior;
- the vLLM endpoint and model ID used, timeouts, token budget, fallback context profile, concurrency and queue bound. Decide whether the service waits for #26 to secure the endpoint or uses the in-cluster Service in the meantime, with the risk recorded;
- which evidence sources are `UNAVAILABLE` in v1 (logs; traces and metrics until RBAC is approved) and how the analysis states this;
- the structured output schema and how invalid, truncated or refused completions map to typed statuses;
- the evaluation dataset format and where it lives (in `box1-docs` run state or the service repo's test resources, never `box1-gitops`).

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Every evidence source classified as available, needs-approval or unavailable, with evidence; MCP extension compatibility confirmed |
| 2 Contracts | Consumer groups for `agentic-operations` declared in `box1-ops-contracts`; no local copy of event schemas |
| 3 Implementation | REST and MCP call one service layer; no write, shell, Kubernetes or arbitrary-URL capability in any tool; deterministic mock-model tests pass |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | Security pass covers MCP authorization, prompt injection and role leakage; the full suite is rerun after repairs |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | After approval, a seeded ERP slowdown (`erp-delayed-processing` through the scenario controller) analyzed through REST and an MCP client on the cluster, with cited evidence and a model-down check |

**Verification scenarios:**

- seeded ERP slowdown with evidence present, and with a source missing;
- model down, model timeout, truncated output and invalid JSON;
- concurrent analyses beyond the queue bound;
- prompt injection in a runbook reference, a Kafka event payload and an order note or field;
- an operator role and a customer role asking about another customer's order;
- an analysis that proposes a rollback, checked to confirm nothing is executed;
- anonymous REST and MCP calls, a call without the role, an unknown MCP tool and invalid tool arguments;
- the same incident through REST and MCP;
- a restart: the earlier analysis ID expires cleanly, and the window refills;
- a poison Kafka record skipped and counted, and a duplicate event deduplicated;
- Kafka unavailable, with readiness and REST still answering;
- tool-call audit metadata complete and free of evidence content.

## Agent finish-line checklist

- Add/update OpenAPI, the MCP tool catalog, relevant event schema fixtures, tests, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
