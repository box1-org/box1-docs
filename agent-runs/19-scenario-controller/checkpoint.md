# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 02:30 EST
- **Phase:** 0–5 complete. **Stopped (stop 2) at Phase 6 entry**: every next action needs approval (`open-decisions.md` A-1 to A-11, decisions O-11, O-13, O-14).
- **Branches and commits:**
  - scenario-controller `run19-controller` `7f0f9ea` (PR #1, CI Succeeded `scenario-controller-validate-std6t`);
  - inventory-service `run19-fixture-admin` `fca04be` (PR #3, CI Succeeded `inventory-service-validate-8hlzm`);
  - box1-gitops `run19-scenario-controller-keycloak` `63c0624` (PR #78);
  - box1-workloads-dev `run19-scenario-controller-runtime` `4c039d3` (PR #103);
  - run state `agent-run/19-scenario-controller`.
  - Nothing is merged or deployed. The cluster still runs the scaffold image.
- **Tests:**
  - controller CI set passes;
  - controller containers set: 48 + 5 IT pass;
  - inventory: 74 + 10 IT pass;
  - local end to end: 37/37 after review (`evidence/07`);
  - CLI exercised (`evidence/07`).
- **Reviews:** five passes, 57 findings, all fixed or recorded (`review-findings/outcomes.md`). The Release pass runs after deployment.
- **Ledger:** 5 `ci_verified`, 21 `locally_tested`, 2 `implemented`, 3 `proposed` (LIVE-*), 1 `blocked` (VS-REDALERT-STOPALL).
- **Local stack:** the `run19-*` containers and four JVMs are running. Tear down with `evidence/scripts/stack.sh down`.

## Exact next action

When the user approves A-1 and A-3:
1. Merge inventory-service#3, then scenario-controller#1.
2. Watch the release runs (`*-release-*` in `box1-ci`) and the promotion PRs.
3. Record the image digest, the GitOps commit and the Argo state.
4. Run the Release reviewer pass.

Then, as each is approved:
1. A-4: merge box1-gitops#78 and check the roles on the cluster.
2. A-5: the user provisions the Secret.
3. A-6: merge box1-workloads-dev#103 and check that the pod's gates report allowed (a 403 without a role, a 200 catalog with one).
4. A-8: seed.
5. A-9 to A-11: the live runs, each recorded in `evidence/` with its run JSON and audit.
