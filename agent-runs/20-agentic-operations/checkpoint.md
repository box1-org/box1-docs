# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

Phase 4 is complete locally (2026-11-06 23:10 EST).

- Service PR [agentic-operations#1](https://github.com/box1-org/agentic-operations/pull/1) is open at `bed8e44`. CI `agentic-operations-validate-9wksz` was running at this checkpoint.
- Ledger: 14 requirements `locally_tested`, 2 `superseded`.
- Evidence: `evidence/04` (58 tests and the evaluation report) and `evidence/05` (production-profile jar and live model probe).

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

1. Confirm that CI on agentic-operations#1 passes. Record the result in `evidence/06-ci.md`, and move ledger entries to `ci_verified` if it does.
2. Phase 5: run the reviewer passes (architecture, messaging, security, operations, release) in fresh subagents, using the diff `61bcb8c..issue-20-agentic-operations`, the prompt and the contracts. Persistence is not applicable because there is no database. Record each pass in `review-findings/`, repair what they find, and rerun `./mvnw -B -ntp verify`.
3. Open three PRs. Each needs the user's approval before merge:
   - box1-ops-contracts: the `TOPICS.md` group change (Q-7);
   - box1-gitops: the `agentic-operations` and `agentic-operations-cli` KeycloakClients (Q-5);
   - box1-workloads-dev: runtime env, resources, replicas 1, ServiceMonitor and PrometheusRule.
4. Raise the anonymous public vLLM route on #26, after the user agrees.

Still open: Q-5 (Keycloak PR), Q-6 (deferred RBAC) and Q-7 (contracts PR).
