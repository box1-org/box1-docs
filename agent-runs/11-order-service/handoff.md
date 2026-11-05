# Agent handoff: stop 6, Phase 7, image fixes for the gate

## Work completed

- Service / platform workstream: Service 01, Order service (box1-docs#11), `frontier` profile.
- Slice / requirements: the whole prompt, delivered. Live acceptance is partial; see `requirements.yaml`.
- Repository and branch: see `checkpoint.md`.
- Changed paths: `order-service`: `src/main/java/org/box1/order/`, `src/main/resources/db/migration/`, `src/main/resources/application.properties`, `src/test/java/org/box1/order/`, `docs/`, `README.md`, `mkdocs.yml`, `pom.xml`. Contracts: `openapi/`, `events/v1/`, `fixtures/`, `ORDER-STATE.md`, `TOPICS.md`, `postgres/OWNERSHIP.md`, `scripts/validate.mjs`, `test/`. Workloads: `workloads/order-service/`. GitOps: `platform/kafka/`.
- PR / commit: [order-service#1](https://github.com/box1-org/order-service/pull/1), [box1-ops-contracts#3](https://github.com/box1-org/box1-ops-contracts/pull/3), [box1-gitops#52](https://github.com/box1-org/box1-gitops/pull/52), [box1-workloads-dev#50](https://github.com/box1-org/box1-workloads-dev/pull/50). All merged by the user. Also open: [box1-templates#23](https://github.com/box1-org/box1-templates/pull/23), then [#24](https://github.com/box1-org/box1-templates/pull/24).

## Tests and deployment proof

- Exact commands and observed results: `./mvnw clean verify -Pcontainers -DskipITs=false`: 72 tests, 0 failures, SpotBugs 0, Checkstyle 0.
- CI status: `order-service-validate-vzxnp` passed at `078f341`: 33 tests. Failure scenarios do not run in CI.
- GitOps PR and deployed image digest: `box1-workloads-dev#51`, `sha256:fb669bff0e522c8067c4118c7ac04303a520acd67a20be85ee940d36344583fd`. The pod's imageID matches.
- Routes / endpoints verified: `POST` and `GET` `/api/v1/orders`, timeline, `/api/info`, health and metrics; see `evidence/07-live.txt`.

## Contract state

- OpenAPI / event schemas changed: yes, `box1-ops-contracts#3`.
- Database migrations and forward compatibility: `V1__order_schema.sql`, not applied anywhere yet. Rollback is forward-only.
- Consumer compatibility / pending follow-up: no consumer exists. `pom.xml` pins contract tests to the PR's head commit; repin after merge if its SHA changes.

## Operations and safety

- Secrets externalized / auth boundaries: the Secret is still declared inline (D-016). No API authentication (box1-docs#40).
- Telemetry evidence: local only. JSON logs carry `orderId`, `traceId` and `correlationId`. No trace backend exists.
- Resource settings: application 100m/256Mi requests and 1/512Mi limits, heap 50%. PostgreSQL 50m/128Mi and 1/512Mi. Workstation sample only.
- Known risks and recovery/rollback: see `checkpoint.md`. Roll back by reverting the promotion commit in `box1-workloads-dev`.

## Next agent session

**Next smallest slice:** see the exact next action in `checkpoint.md`. Merge `order-service#3` so the release runs with `gate`. Separately, merge `box1-templates#23`, ship its plugin image, and merge `#24`.

- Exact files to read: `checkpoint.md`, `decisions/D-016-secrets-integration-choice.md`, `requirements.yaml`, the prompt and profile from `box1-docs` `origin/main`.
- Blockers and required user decisions: merge `order-service#3`; template merges. Scanner and eviction work is box1-docs#43. Vault is deferred to box1-docs#41.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#11
current_phase: 7
repositories:
  - name: order-service
    branch: order-domain
    commit: 078f341e9014a38daf826719cf67b5bf8f4fc6bd
  - name: box1-ops-contracts
    branch: order-service-v1-additions
    commit: 7dcf2909dfccf6e0009504d6542bdb45a647a68b
  - name: box1-workloads-dev
    branch: order-service-runtime-config
    commit: de4a2188df4db36235c662172d3f03ab7f32cc2e
  - name: box1-gitops
    branch: order-dlq-topic
    commit: fe11b0f319dc18a196526a64ff9e4e3facd287d6
run_state_path: agent-runs/11-order-service/
requirements:
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 23
  live_verified: 10
  blocked: 1
  superseded: 1
image_digest: sha256:fb669bff0e522c8067c4118c7ac04303a520acd67a20be85ee940d36344583fd
gitops_commit: 5fd61de2479b899ab4f6e9e48055c527f13ac632
review_passes_completed: [architecture, persistence, messaging, security, operations]
open_decisions: []
rollback_state: revert the promotion commit; V1 stays applied
next_action: Merge order-service#3, follow the gated release, then run the Release pass
```
