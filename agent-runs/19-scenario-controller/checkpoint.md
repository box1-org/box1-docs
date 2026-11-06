# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 ~02:15 EST
- **Phase:** 4 Verification complete. Next: 5 Review (reviewer subagents).
- **Branches:**
  - scenario-controller `run19-controller` `e061f6d` (PR #1, CI pending at last check);
  - inventory-service `run19-fixture-admin` `fca04be` (PR #3, CI passed);
  - run state `agent-run/19-scenario-controller`.
- **Tests:**
  - controller: CI set 19 (now 22 with ContractTest) pass; containers 38 + 5 IT pass (`evidence/03`).
  - inventory: 74 + 10 IT pass.
  - local end to end against the real services and ERP harness: all steps pass (`evidence/04`).
- **Ledger:**
  - most AC/VS entries are `locally_tested`;
  - VS-REDALERT-STOPALL is `blocked`;
  - LIVE-* are `proposed`;
  - SC-NOEXEC, SC-CLI and SC-OBS are `implemented`.
- **Platform change:** P-3 is superseded (adapter SFTP to the ERP is live, `evidence/05`). LIVE-GUIDED-ERP via `erp-manual-hold` is feasible once the controller is deployed.
- **Local stack:** `run19-*` containers and four JVMs are still running for possible reruns. Tear down with `evidence/scripts/stack.sh down`.
- **Still open for the user:**
  - O-3 identity (Keycloak clients `scenario-controller` and `inventory-service`, client secret);
  - O-11 database credential;
  - every merge (inventory-service#3, scenario-controller#1, the workloads PR, the Keycloak PR);
  - the contract patch;
  - cluster seeding and each cluster run.

## Exact next action

Run the Phase 5 reviewer passes (architecture, persistence, messaging/integration, security, operations) as fresh read-only subagents on `run19-controller` `e061f6d` and inventory-service#3, then fix in-scope findings, rerun both suites and the end-to-end check, and record `review-findings/`. Then prepare (do not merge) the box1-workloads-dev PR (gates, upstream URLs, POD_NAMESPACE, token Secret reference) and the box1-gitops Keycloak PR, and stop for approvals.
