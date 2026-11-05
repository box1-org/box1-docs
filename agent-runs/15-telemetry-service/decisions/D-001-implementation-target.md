# D-001 Implementation target

**Status:** resolved by the user, 2026-11-05 18:03 EST, in the run request.

## Question

The prompt proposes `box1-org/box1-ops-telemetry`. Its Frontier section records that `box1-org/asset-service` was created through the Golden Path (template 1.1.0) on 2026-11-05 with this issue's mission text, and asks the agent to confirm with the user.

## Decision

Build in `box1-org/asset-service`. Do not create `box1-ops-telemetry`.

The user onboarded `asset-service` through the Golden Path for this issue and named it as the implementation target in the run request. This is recorded as a resolved decision, not as a conflict stop.

## Consequences

- Namespace `asset-service-dev`, Route `asset-service-dev.apps.ocp.box1.org`, workload path `box1-workloads-dev/workloads/asset-service/`.
- The Keycloak client ID, Kafka consumer group and metric prefixes follow the repository name (`asset-service`), not `telemetry`. Topic names keep the contract's `box1.telemetry.*` names.
- Standing permission covers branches, commits, pushes and PRs in `asset-service`, `box1-ops-contracts`, `box1-workloads-dev` and `box1-gitops`. Merges need approval one at a time.
