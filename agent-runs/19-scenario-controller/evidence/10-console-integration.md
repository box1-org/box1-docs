# Operations console integration, 2026-11-06 ~14:20–14:45 EST

**Decision:** D-012.

**PRs (all open, none merged):**
- box1-org/operations-console#7 (`c22ee91`)
- box1-org/box1-gitops#81
- box1-org/box1-workloads-dev#116
- box1-org/scenario-controller#2 (docs)

## Unit and contract tests (operations-console)
- `./mvnw verify` ran 61 tests with 0 failures; Checkstyle 0, SpotBugs 0. The frontend type-checks and builds.
- **`ScenarioControlTest`** (12 tests, WireMock) checks that:
  - the bearer goes to the controller only; inventory requests carry no `Authorization`;
  - `/me` reports the scenario roles;
  - with no session token, nothing is forwarded and the refusal is explained;
  - start sends the TTL, a correlation ID and a traceparent;
  - controller 409/403/404 map to `SCENARIO_CONFLICT`, `SCENARIO_ROLE_REQUIRED` and `NOT_FOUND`, with the controller's own detail;
  - a connection reset gives 503 "outcome unknown";
  - names, run IDs, steps and TTLs are validated before any call;
  - a viewer gets 403 on every action and the controller is never called;
  - stop, reset, seed, confirm, runs, run, audit and fixtures are mapped.
- **Test repair:** a new test read `/api/v1/sites` without stubbing asset-service. That cached an OK telemetry probe for 60 s and failed an existing test. The new test now stubs asset-service as refusing, as on the cluster.

## Local end to end against the real services
- **Setup:** `scripts/console-client.sh` added the console client to the local Keycloak 26.4, shaped like #81. `stack.sh console` started the console on 39085 against:
  - the real controller (restarted with `SCENARIO_ALLOWED_AZP=scenario-controller,operations-console`);
  - order, inventory and fulfillment;
  - the ERP harness.
- **Clocks:** host and Podman VM both read 19:30:29 UTC.
- **Spec:** `scripts/console-e2e/scenarios.spec.ts`, Playwright 1.65.0, Firefox. It fails on any CSP violation or page error.

| Check | Result |
|---|---|
| Operator: 10 cards (5 available), titles, not-yet-possible reason; seed; start *The Trouble with Tribbles* after confirming; run ends VERIFIED and is reset; audit START under the operator's subject and username | Pass |
| Operator: start *Warp core breach*; the "Your step" text (arm the crash) shows; "I have done this" records CONFIRM `crash-armed` under the operator; stop gives STOPPED with a reset | Pass (second attempt) |
| Viewer: catalog and runs visible; no seed or start buttons | Pass |
| Console operator without a scenario role: explanation shown; the catalog read is refused, with the reason in the sources banner; a forced POST start gets 403 `SCENARIO_ROLE_REQUIRED` from the controller | Pass |

**Repair found by the end-to-end run.** After a confirmation the controller keeps the old step text on the run, while its status returns to RUNNING. The page went on showing the old step as if it were still the operator's task. The page now shows "Your step" only while the run is `AWAITING_OPERATOR`.

The first attempt left a crash run open. It was stopped through the controller (STOPPED, `RESET_GUIDED`, `CAT-DILITHIUM-NIP` restored from 19 to 20). No crash was armed in the ERP.

**Not tested:**
- The cluster: it needs #81 merged and synced, #116 merged, and #7 merged, released and deployed.
- The `erp-manual-hold` console step through the page.
- Token refresh during a long session.

## Delivery, 2026-11-06 ~14:50–15:15 EST (merges and syncs approved by the user: "merge all of them and sync")

| Step | Result |
|---|---|
| box1-gitops#81 | Merged `f257bb6`; Argo `keycloak` Synced/Healthy/Succeeded at `f257bb6`; KeycloakClient `operations-console` `ready=true` |
| box1-workloads-dev#116 | Merged `fe5c091`. Argo `scenario-controller` and `operations-console` both Synced/Healthy at `fe5c091`. Live env: the controller has `SCENARIO_ALLOWED_AZP=scenario-controller-cli,operations-console`; the console has `SCENARIO_CONTROLLER_URL` and `CONSOLE_SCENARIO_FORWARD_TOKEN=true` |
| scenario-controller#2 (docs) | Merged `a44419e`. Release `scenario-controller-release-f8bfl` Succeeded with image `sha256:af7af89f…`; promotion box1-workloads-dev#117 |
| operations-console#7 | The first CI run never started: Pipelines as Code got a GitHub 404 while patching the check run (`pipelinerun start failure`) and left `operations-console-validate-kplrr` pending. A `/retest` comment started `px64t`, which Succeeded. Merged `ed2c1ac`. Release `operations-console-release-jm4cm`: build, security (`gate`; critical 0, high 10), promote, smoke and console-smoke all Succeeded; image `sha256:5ad138dd…`; promotion box1-workloads-dev#118 at `19d9e74`. Argo Synced/Healthy; rollout complete |

**Read-only live checks (anonymous):**
- Console readiness: 200.
- `/api/v1/scenarios` and `/api/v1/scenario-runs` without a session: 401.
- The served OpenAPI includes the new operations.
- The only console log warning is the known per-pod session key (#18 O-3).

**Signed-in live check: not done.** The `claude` test user's password was refused by Keycloak ("Invalid username or password"); it had worked at about 13:20 EST. I did not retry. `scripts/console-e2e/live-readonly.spec.ts` is ready: it signs in, then only reads `/demo`, `/api/v1/me`, `/api/v1/scenarios` and `/api/v1/scenario-runs`.

**Leftover:** the pending PipelineRun `operations-console-validate-kplrr` in `box1-ci`, left by the Pipelines as Code failure, was not deleted.

## Signed-in live check and the seeding 403, 2026-11-06 ~15:00–15:30 EST

**Signed-in check.** The user supplied a new test password. `live-readonly.spec.ts`, run read-only as the test user, found:
- `/api/v1/me`: console roles `console-viewer`, `console-operator`, `console-developer`; scenario roles `scenario-operator`.
- The catalog: 10 items, controller source OK (3 ms), titles shown, 5 AVAILABLE.
- Five Start buttons and no CSP errors.

**Live operator access through the console: verified.**

**The user's seeding failure.** The controller's audit shows:
- SEED FAILED at 19:12Z, "Inventory answered 403 to a site create", actor the user.
- A `baseline-order` run at 19:57Z, FAILED "Fixtures are not seeded", with reset RESET_OK.

**Diagnosis (repair 16).**
- inventory-service needs only audience `inventory-service` and `resource_access.inventory-service.roles`. A 403 therefore means the role is missing from the token.
- The user checked the admin console: `inventory-admin` is assigned to the service account and scope-mapped. The Evaluate token had `scope: openid` and no `resource_access` claim at all.
- Cause: the `scenario-controller` client (#78) listed no `defaultClientScopes`, so the `roles` scope that writes `resource_access` was missing. Every other box1 client lists `roles`.
- Why the local stack missed it: Keycloak 26 gives new clients `roles` by default, and the local client also kept `fullScopeAllowed: true`.

**Fix.** box1-org/box1-gitops#84, merged by the user as `8203a7d`. Argo `keycloak` synced; the CR is `ready=true` with `defaultClientScopes: ["roles"]`.

**Not yet verified:** seeding after the fix. It needs the user to click Seed, or approval for me to do it.
