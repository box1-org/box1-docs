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
