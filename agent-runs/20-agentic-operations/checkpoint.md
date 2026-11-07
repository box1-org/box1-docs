# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

Phase 5 is complete (2026-11-06 23:45 EST).

- **Reviews:** five reviewer passes ran in fresh subagents: architecture, messaging, security, operations and release. Persistence is not applicable. They found no high-severity issues.
- **Repairs:** the in-scope findings are repaired on agentic-operations#1 at `0cf2604` (`evidence/07`). CI `agentic-operations-validate-6lt27` is green, with 69 tests and 5 ITs.
- **Ledger:** 14 requirements `ci_verified`, 2 `superseded`.
- **Open findings:** they need the three platform PRs (M-1/A-3/R-1, R-4, WR-1 to WR-3) or are accepted (M-7, R-2).

## Completed

- The prompt was given a frontier profile and merged: box1-docs PR #96 → `12f0b11`. Issue #20 mirrors it.
- Discovery baseline: `evidence/01-discovery-baseline.md`, covering revisions, the template, Kafka, vLLM, node capacity, the MCP extension, evidence sources, identity and console incidents.
- Decisions D-001 to D-015 in `decisions/`.
- Ledger: 16 entries in `requirements.yaml`. 14 are `proposed`; RAG and the approval workflow are `superseded` by user decision.

## Key findings

- **Live probe bug, fixed:** vLLM answers HTTP 400 when the JDK client offers an h2c upgrade. Both clients are now pinned to HTTP/1.1 (`evidence/05`).
- **Tokens in logs, fixed:** Quarkus OIDC logs raw bearer tokens at WARN when verification fails. That logger is now set to ERROR, and introspection fallback is off (`evidence/05`).

- The vLLM public route `route-purple-bass-vllm.apps.ocp.box1.org` answered an anonymous `GET /v1/models` with **200** (Q-3, #26).
- The MCP extension's stable 2.0.4 is built on Quarkus 3.33.3.1, while services use 3.40.1.1. 2.1.0.Beta1 matches 3.40.1 (Q-2).
- MCP `ToolFilter`s fail open when they throw. Authorization is enforced in the service methods (D-004).
- Telemetry alerts need an asset-service config change (Q-5). Traces and metrics need RBAC (Q-6). Logs do not exist (#82). All are `UNAVAILABLE` in v1.
- The model gets no tools in v1. Evidence is gathered deterministically by the service, which removes injection-driven tool calls (D-006, D-010).

## Branches and worktrees

- box1-docs `agent-run/20-agentic-operations`, worktree `/Users/mike/Documents/ChatGPT/box1/run20-docs`.
- agentic-operations `issue-20-agentic-operations` at `f6a072b` (MCP probe), pushed, no PR. Clone `/Users/mike/Documents/ChatGPT/box1/run20-agentic-operations`.
- No other repository has been touched by this run. Onboarding PRs #146 and #147 came from Developer Hub.

## Open risks

- Using the vLLM endpoint while it is anonymous and public.
- A single replica with in-memory state: analyses are lost on restart, by design. Reconfirmed by the user over PostgreSQL on 2026-11-06 (D-003). Durable state comes with the approval workflow, #97.
- Kafka has no authentication (#71).

## Exact next action

1. Phase 6: open three PRs. Each needs the user's approval before merge:
   - **box1-ops-contracts:** in `TOPICS.md`, rename `ai-operations` to `agentic-operations` on telemetry and add it to the order, inventory, fulfillment and notification rows (Q-7).
   - **box1-gitops:** KeycloakClients `agentic-operations` (confidential, roles `aiops-viewer` and `aiops-analyst`, no upstream grants in v1) and `agentic-operations-cli` (public, PKCE, audience mapper and role scope mapping), following `scenario-controller-client.yaml` and `scenario-controller-cli-client.yaml` (Q-5).
   - **box1-workloads-dev:** `strategy: Recreate`, `replicas: 1`, and Deployment `env` for the runtime URLs, `AIOPS_ALLOWED_AZP`, `AIOPS_CONSUMER_GROUP` and the OTel attributes. Also a ServiceMonitor and a PrometheusRule (model unavailable, window not refilling, pod down), copied from notification-service.
2. Link the three PRs from agentic-operations#1.
3. After the user merges them in order, merge #1, then watch the release, promotion, digest and Argo.
4. Phase 7, live acceptance, after approval:
   - `erp-delayed-processing` through the scenario controller, analyzed through REST and through an MCP client;
   - the anonymous 401 checks, the trace linkage, the window refill time, and `oc adm top` during the replay.
5. File a follow-up for per-service release smoke checks (R-2). Raise the anonymous vLLM route on #26, once the user agrees.

Still open: Q-5 and Q-7 (PR approvals) and Q-6 (deferred RBAC).
