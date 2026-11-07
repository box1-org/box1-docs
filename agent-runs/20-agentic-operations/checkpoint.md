# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

Phase 3 (implementation) started at 2026-11-06 22:40 EST. The user onboarded the service (Q-1). MCP 2.0.4 is proven on Quarkus 3.40.1.1 (Q-2, `evidence/03`). The template scaffold is live (`evidence/02`).

## Completed

- The prompt was given a frontier profile and merged: box1-docs PR #96 → `12f0b11`. Issue #20 mirrors it.
- Discovery baseline: `evidence/01-discovery-baseline.md`, covering revisions, the template, Kafka, vLLM, node capacity, the MCP extension, evidence sources, identity and console incidents.
- Decisions D-001 to D-015 in `decisions/`.
- Ledger: 16 entries in `requirements.yaml`. 14 are `proposed`; RAG and the approval workflow are `superseded` by user decision.

## Key findings

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

Implement D-002 to D-012 on `issue-20-agentic-operations`, in this order:

1. evidence clients and `EvidenceService` with `@RolesAllowed`;
2. the Kafka window;
3. the model client and a mock;
4. `AnalysisService` and the REST resource;
5. replace the probe with the MCP tool catalog;
6. the evaluation fixtures.

Then run `./mvnw -B -ntp verify`.

Still open: Q-3 (vLLM endpoint use), Q-4 (operator-only), Q-5 (Keycloak PR), Q-6 (deferred RBAC) and Q-7 (contracts PR).
