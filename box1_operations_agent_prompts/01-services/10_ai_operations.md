# Service 10 — AI Operations service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · AI-01/02/03; P1 · AI-04/05/06/07/08

**Dependencies:** Read-only evidence APIs/observability, versioned vLLM inference API, OIDC identity, optional runbook index.

## Mission and boundary

Own the **evidence-grounded incident-analysis workflow**, not cluster administrator privileges. Proposed repo `box1-org/box1-ops-ai`. Local Qwen/vLLM is a replaceable model inference layer; it is *not* the source of truth for current cluster state. Agents may implement orchestrator using Quarkus where practical or justify a Python service only if ecosystem requirements materially benefit.

## Interfaces, domain behavior and implementation constraints

- `POST /api/v1/ai/incidents/{id}/analyze` submits a bounded analysis request and returns operation ID; `GET /api/v1/ai/analyses/{id}` returns status, summary, findings, confidence/uncertainty, evidence entries and suggested (not executed) actions. Response requires evidence ref ID, type, source, timestamp, retrieval status and a safe URL or trusted identifier for every material claim.
- Evidence tool registry limited to scoped GET/read-only interfaces: order timeline, fulfillment status, relevant metrics/alerts, approved logs/traces, deployment Git SHA/change record and runbook passages. Validate caller RBAC **server-side** before tool invocation. Never pass a kubeadmin token to model or allow arbitrary shell/Kubernetes API actions.
- Retrieval P1: ingest approved runbooks/deployment notes; chunk, embed/index with source version, timestamp, ACL and expiry; show freshness and source in answer. Treat retrieved text/tool outputs as untrusted data (prompt injection tests).
- Model API config external (`VLLM_BASE_URL`, `MODEL_ID`, timeout, maximum evidence bytes, max output tokens). Use only versioned inference API and explicit structured JSON schema parsing/validation; handle truncated/invalid completions, timeouts and model unavailability without fabricated analysis.
- For nominal 64K model context: allocate bounded system policy + tool schema + concise selected evidence; dedupe/re-rank evidence; reserve output and cache. Model server's configured 64K is not guaranteed on 32 GB VRAM. Add fallback to 16K/32K context or small model; limit concurrency and log token budgets (without content secrets).
- Remediation approval is a separate backend state machine: `PROPOSED` → `APPROVED` → `EXECUTED` / `REJECTED`, human actor bound, action allowlist, dry-run / expected effect / rollback plan. **First iteration only proposes actions**; no write-capable connector until independently authorized.
- Evaluation dataset: known slow ERP, inventory denial, broker outage, healthy control and missing/conflicting evidence. Score citation coverage, unsupported assertions, role leaks, prompt injection refusal, tool errors and p95 analysis time. Log tool invocation metadata and policy decisions, not raw secrets.

## Acceptance evidence (automate where practical)

- Given seeded ERP slowdown, returns specific ERP adapter evidence and a real trace/alert/deployment reference if provided; if source absent, explicitly says evidence unavailable.
- Prompt injection embedded in runbook and logs cannot cause new privileges, extra data disclosure or unsupported tool calls.
- No cross-tenant/customer data leakage across operator and customer roles.
- Model downtime returns typed degraded/unavailable status and never an invented diagnosis.
- User pressing “analyze” cannot execute rollback or arbitrary remediation; proposal and actual execution remain separate.

## Recommended 64K-safe implementation slices

1. Evidence API/role authorizer + deterministic mock-model tests.
2. vLLM client, bounded prompt assembly and strict structured response parsing.
3. Citation/evidence formatting and failure/unknown states.
4. Optional RAG runbook indexing with ACL/freshness and injection tests.
5. Approval proposal records and evaluation harness (no autonomous writes).

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
