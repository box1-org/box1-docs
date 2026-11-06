# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 ~01:25 EST
- **Phase:** 0 Discovery, complete. **Stopped (stop 1)** at the Phase 0 exit: the user asked to see the mechanism classification before design, and several product/authority decisions are open (`open-decisions.md` O-1 to O-12).
- **Branches and commits:** box1-org/scenario-controller `main` `203968e` (scaffold, untouched; clone at `/Users/mike/Documents/ChatGPT/box1/run19-scenario-controller`). Run state on box1-docs `agent-run/19-scenario-controller` (worktree `run19-docs`).
- **Changed files:** run state only (`run.json`, `requirements.yaml`, `checkpoint.md`, `open-decisions.md`, `pilot-log.md`, `decisions/D-001..D-005`, `evidence/00-discovery.md`, `evidence/01-mechanism-classification.md`).
- **Tests:** none run yet.
- **Ledger:** all entries `proposed`.
- **Open risks:** scenario-controller's PostgreSQL credential (#41 pattern; reported to the user directly); broker accepts unauthenticated clients (reported directly); the order → reservation chain is unproven on the cluster (P-6).

## Exact next action

When the user answers O-1 (and O-2, O-3, O-10 where they choose to): write the Phase 1 design decisions (catalog schema, allowlist, auth, audit and retention, TTL and crash recovery, stardate, console adoption) against the accepted classification. Then implement the controller core with local proofs for every scenario the classification marks locally provable, using `run19-*` containers and avoiding ports 15432, 19092 and 18180.
