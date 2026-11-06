# D-006: Demo namespace allowlist is `scenario-controller-dev`

- **Status:** decided under the user's delegation, 2026-11-06 ("i dont know what this is, go for it").
- **What it is:** the list of namespaces in which the controller will run any scenario. Outside it, every start, stop and reset is refused and audited. It is the gate required by `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`.
- **Decision:** `SCENARIO_NAMESPACE_ALLOWLIST=scenario-controller-dev` and `SCENARIO_ENVIRONMENT=dev`. The controller reads its own namespace from the downward API (`POD_NAMESPACE`) and refuses if it is unset or not listed, so a copy deployed elsewhere fails closed. Both `SCENARIO_CONTROL_ENABLED=true` and the allowlist are required (two gates, as in #15).
- **Not implied:** this approves no cluster seeding and no scenario run. Each still needs the user's approval.
