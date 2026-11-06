# D-010 Demo control

**Status:** decided: **deferred until #19 exists.**

- The "Demo control" page reports that the scenario controller (#19) is not deployed (`sources: scenario-controller NOT_CONFIGURED`). It offers no start or stop actions.
- It links to the asset telemetry console (`https://asset-service-dev.apps.ocp.box1.org/console/`), which owns telemetry load and chaos, with a note that it needs that service's `chaos-operator` role. Nothing from that console is duplicated.
- The console creates no admin role and no fault endpoints, and holds no kubeconfig.
