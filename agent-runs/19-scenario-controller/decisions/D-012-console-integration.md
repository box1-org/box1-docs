# D-012: Operations console drives the scenario controller with the person's token

**Date:** 2026-11-06 (America/New_York). **Decided by:** the user ("Integrate this with the operations-console"). They chose "Forward user token" and "Full control" when asked.

## Decision
- The console's Demo control page (box1-org/operations-console#7) offers the full scenario surface:
  - catalog, seed, start with an inline confirmation, stop, reset;
  - the active run's operator step, and confirmations of steps the controller cannot observe;
  - recent runs, the audit trail and the fixtures.
- The console forwards the signed-in person's access token **to the scenario controller only** (`CONSOLE_SCENARIO_FORWARD_TOKEN`). Every other upstream keeps #18's no-token rule.
- The `operations-console` Keycloak client gains the `scenario-controller` audience and a scope mapping for `scenario-viewer` and `scenario-operator` (box1-org/box1-gitops#81). The controller accepts `azp=operations-console` (box1-org/box1-workloads-dev#116). The controller needs no code change.
- To act, a person needs `console-operator` in the console and `scenario-operator` on the controller. The controller enforces its role and records the person (subject and username) in its audit.

## Trade-off
This reverses #18's SEC-1 rule for one audience. Any realm user who signs in to the console holds a token with `aud` including `scenario-controller`. Without a scenario role, the controller refuses that token (403), so the exposure is the same as `scenario-controller-cli`'s.

## Alternative not taken
A confidential console client with a service account. It needs a new secret, and the controller's audit would name the console instead of the person.

## Ownership
- operations-console is #18's repository; the user's request authorized this change. Run #18 is stopped, and its clone and branches were not touched.
- The work is in clone `run19-operations-console`, branch `run19-scenario-control`.
