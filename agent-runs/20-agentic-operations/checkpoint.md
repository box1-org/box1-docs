# Checkpoint: box1-docs#20 agentic-operations (frontier)

## Current phase

**Phase 7 is partly done** (2026-11-07 00:50 EST, `evidence/10-live-acceptance.md`). Live REST and MCP analysis of a real order: cited evidence, identical evidence through REST and MCP, trace across 4 services, clean audit logs. The token came from a device login approved by `mike`. Ledger: 5 `live_verified`, 9 `deployed`, 2 `superseded`. The seeded ERP slowdown waits for the user's approval.

**Phase 6 is complete** (2026-11-07 00:35 EST). See `evidence/09-delivery.md`.

- **Merged:** all four PRs. The service is live at `9d2d3e3`.
- **Digest:** `sha256:21da40d4…` matches across GitOps and the pod. `/api/info` reports the same revision, and Argo is Synced/Healthy.
- **Live checks:** anonymous calls get 401 on REST and `/mcp`. The Kafka window is filling from the real broker (144 events across 18 partitions).
- **Ledger:** 14 requirements `deployed`, 2 `superseded`.
- **Known issue:** the release PipelineRun is marked `CouldntGetPipelineResult`. All its tasks succeeded, but `SCAN_OUTPUT` is missing because security gates are disabled by the template default (#42). The image went out without an ACS or TPA check.

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

1. With the user's approval, run `erp-delayed-processing` through the scenario controller in its allowlisted demo namespace (see 09_scenario_controller.md). Analyze the resulting `AWAITING_ERP_TOO_LONG` incident through REST and MCP, then stop or reset the scenario. Record this in `evidence/11`, then move AIO-ERP-001 and AIO-MODEL-related entries up if they are proven.
2. Optional, needs approval: a pod restart, to observe the analysis 404 and the window refill live.
3. Follow-ups to propose to the user:
   - the `SCAN_OUTPUT` false failure (on #42);
   - per-service release smoke checks (R-2);
   - the anonymous public vLLM route (on #26);
   - MCP requests have no server span;
   - RAG and persistent state are #97.
4. Handoff (`05_HANDOFF_TEMPLATE.md`), then the achievement log when the user asks.
