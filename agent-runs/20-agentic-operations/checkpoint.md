# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

**Phase 6 is in progress** (2026-11-07 00:10 EST). All four PRs are open, with checks green, and are waiting for the user's merge approval (`evidence/08-platform-prs.md`).

Phase 5 summary follows.

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

1. The user approves the merges, in this order, with about 10 seconds between them:
   1. box1-ops-contracts#13
   2. box1-gitops#99
   3. box1-workloads-dev#153
   4. agentic-operations#1
2. After #99 syncs, check the clients, roles and scope mapping in Keycloak, and the token claims. The user assigns the `aiops-*` roles.
3. After #1 merges, watch the release PipelineRun and the promotion PR. Then confirm the digest in box1-workloads-dev, Argo Synced/Healthy and the running pod's imageID. Also check that `/api/info` `gitRef` equals the merge commit.
4. Phase 7, live acceptance, after approval:
   - anonymous 401 on `/api/v1/ai/*` and `/mcp`;
   - `erp-delayed-processing` through the scenario controller, analyzed through REST and through an MCP client;
   - trace linkage in Tempo;
   - window refill time and `oc adm top` during the replay.
5. File a follow-up for per-service release smoke checks (R-2). Raise the anonymous vLLM route on #26, once the user agrees.
