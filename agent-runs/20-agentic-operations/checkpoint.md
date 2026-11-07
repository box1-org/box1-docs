# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

Phases 0 (discovery) and 1 (design) are complete as of 2026-11-06 22:30 EST. **The run is stopped at an approval boundary.** Phase 3 needs the repository, and onboarding it is approval-required (Q-1).

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
- No other repository has been touched.

## Open risks

- Using the vLLM endpoint while it is anonymous and public.
- A single replica with in-memory state: analyses are lost on restart, by design.
- Kafka has no authentication (#71).

## Exact next action

The user answers `open-decisions.md`, at minimum Q-1. After onboarding:

1. clone `box1-org/agentic-operations` to `run20-agentic-operations`;
2. branch `issue-20-agentic-operations`;
3. add `quarkus-mcp-server-http` and `-oidc` 2.0.4 and run `./mvnw -B -ntp verify` to settle Q-2;
4. then implement following D-002 to D-012.
