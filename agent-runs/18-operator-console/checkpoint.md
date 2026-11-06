# Checkpoint: box1-docs#18 operator console (frontier)

**Current phase:** stopped at the **Phase 6 entry**. The next action needs the user's approval.
**Updated:** 2026-11-06 ~00:05 EST.

## Done
- **Phases 0–5 complete.** Discovery, design (D-001…D-015 with amendments), contract, implementation, local and CI verification, and five reviewer passes (43 findings) with repairs. The full suite was rerun after the repairs.
- **operations-console** `issue-18-console` @ `1d65b2b`, PR #2.
  - CI: `operations-console-validate-8pkct` green (50 unit/HTTP + 5 IT, Checkstyle 0, SpotBugs 0).
  - Playwright Firefox 15/15 locally.
- **box1-gitops#73** @ `16d561e`: KeycloakClient with its own audience only and an exact `/callback` redirect.
- **box1-workloads-dev#90**: Deployment env.
- **Ledger:** 12 ci_verified, 19 locally_tested, 3 implemented, 1 blocked (customer role), 1 proposed (delivery). Nothing is deployed or live-verified yet.
- **Local stack stopped.** No run18 containers or processes are running.

## Exact next action (after approval)
1. Merge box1-gitops#73. Confirm Argo `keycloak` synced and the three client roles exist (`oc get keycloakclient -n keycloak operations-console`). The user assigns roles.
2. Merge box1-workloads-dev#90. Argo auto-syncs; check the pod rolls and stays Ready.
3. Merge operations-console#2. Watch `operations-console-release-*`:
   - build;
   - gate (`gate` enforcement; first gated run for this service);
   - promote PR (auto-merged after checks);
   - smoke;
   - console-smoke.
   Record the digest and GitOps commit.
4. Phase 7 on the real Route, in Firefox:
   - sign-in;
   - 401 and 403 through the Route;
   - token absence, logout, pod restart;
   - axe, keyboard, mobile;
   - one order followed with ERP progress, after fixture approval (O-6).
   The held-ERP part is blocked by G-3.

## Open decisions
`open-decisions.md` O-1…O-9.
