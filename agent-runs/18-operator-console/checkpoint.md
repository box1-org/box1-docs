# Checkpoint: box1-docs#18 operator console (frontier)

**Current phase:** 5 Review. Four reviewer subagents are running against operations-console `d007f00`: security; architecture with persistence/messaging; operations with release; front end/a11y.
**Updated:** 2026-11-05 ~23:40 EST.

## Done
- **Phase 0** discovery: `evidence/00-discovery.md`. Front-end build probe CI-verified: `evidence/01`.
- **Phase 1** design: `decisions/D-001`…`D-015`, `open-decisions.md`.
- **Phase 2** contract: `evidence/02-contract.md`.
- **Phase 3** implementation on operations-console `issue-18-console`:
  - `77c8da1` backend, `4af6381` front end and e2e, `d007f00` docs.
  - PR box1-org/operations-console#2.
- **Phase 4** verification:
  - Maven 45+5 green locally and in CI (`operations-console-validate-l6jv2`).
  - Playwright Firefox 14/14 locally: `evidence/03`, `evidence/04`.
- **GitOps PRs (open, unmerged):** box1-gitops#73 (Keycloak client), box1-workloads-dev#90 (Deployment env).
- **Ledger:** 11 ci_verified, 20 locally_tested, 3 implemented, 1 blocked, 1 proposed.

## Branches, worktrees, local processes
- box1-docs `agent-run/18-operator-console`: worktree `/Users/mike/Documents/ChatGPT/box1/run18-docs`.
- operations-console clone: `/Users/mike/Documents/ChatGPT/box1/run18-operations-console`, branch `issue-18-console`.
- box1-gitops worktree `run18-gitops` (branch `run18-operations-console-keycloak`); box1-workloads-dev worktree `run18-workloads` (branch `run18-operations-console-runtime`).
- Local e2e stack may still be up:
  - `RUN_DIR=/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/643d6884-2ad5-4a10-8c89-e80e450a183b/scratchpad/run18-e2e`
  - stop with `src/test/e2e/local-down.sh`
  - container `run18-keycloak`; stub and console PIDs in RUN_DIR.
- Pinned Node for local npm: `…/scratchpad/node-v24.22.2-darwin-arm64/bin`.

## Exact next action
When the reviewer reports arrive:
1. Write `review-findings/{security,architecture,persistence,messaging,operations,release,frontend}.md`.
2. Fix in-scope findings on `issue-18-console`.
3. Rerun the full Maven suite and the Playwright suite (phase-exit requirement).
4. Push, confirm PR CI, and update the ledger and pilot log.
5. Then Phase 6 needs user approvals (merges), so stop and report all open decisions together.

## Open risks and decisions
- `open-decisions.md`: O-1…O-8 (G-1 link, G-2 asset azp, O-3 session key, O-4 favicon, O-5 customer role, O-6 fixtures, O-7 Keycloak merge and role assignment, O-8 no held ERP on the cluster).
- Build egress to nodejs.org and npmjs.org is observed, not guaranteed.
