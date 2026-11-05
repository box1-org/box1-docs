# Agent handoff: stop 2, Phase 6 entry

## Work completed

- Service / platform workstream: Service 01, Order service (box1-docs#11), `frontier` profile.
- Slice / requirements: the whole prompt through review. Not delivered or live.
- Repository and branch: see `checkpoint.md`.
- Changed paths: `order-service`: `src/main/java/org/box1/order/`, `src/main/resources/db/migration/`, `src/main/resources/application.properties`, `src/test/java/org/box1/order/`, `docs/`, `README.md`, `mkdocs.yml`, `pom.xml`. Contracts: `openapi/`, `events/v1/`, `fixtures/`, `ORDER-STATE.md`, `TOPICS.md`, `postgres/OWNERSHIP.md`, `scripts/validate.mjs`, `test/`. Workloads: `workloads/order-service/`. GitOps: `platform/kafka/`.
- PR / commit: [order-service#1](https://github.com/box1-org/order-service/pull/1), [box1-ops-contracts#3](https://github.com/box1-org/box1-ops-contracts/pull/3), [box1-gitops#52](https://github.com/box1-org/box1-gitops/pull/52), [box1-workloads-dev#50](https://github.com/box1-org/box1-workloads-dev/pull/50). None merged.

## Tests and deployment proof

- Exact commands and observed results: `./mvnw clean verify -Pcontainers -DskipITs=false`: 72 tests, 0 failures, SpotBugs 0, Checkstyle 0.
- CI status: `order-service-validate-vzxnp` passed at `078f341`: 33 tests. Failure scenarios do not run in CI.
- GitOps PR and deployed image digest: none observed. The deployed image is still the scaffold.
- Routes / endpoints verified: none for this code.

## Contract state

- OpenAPI / event schemas changed: yes, `box1-ops-contracts#3`.
- Database migrations and forward compatibility: `V1__order_schema.sql`, not applied anywhere yet. Rollback is forward-only.
- Consumer compatibility / pending follow-up: no consumer exists. `pom.xml` pins contract tests to the PR's head commit; repin after merge if its SHA changes.

## Operations and safety

- Secrets externalized / auth boundaries: the Secret is still declared inline (D-016). No API authentication (box1-docs#40).
- Telemetry evidence: local only. JSON logs carry `orderId`, `traceId` and `correlationId`. No trace backend exists.
- Resource settings: application 100m/256Mi requests and 1/512Mi limits, heap 50%. PostgreSQL 50m/128Mi and 1/512Mi. Workstation sample only.
- Known risks and recovery/rollback: see `checkpoint.md`. No cluster state changed, so there is nothing to roll back.

## Next agent session

**Next smallest slice, in order. Each merge and the operator install needs the user's approval, one at a time:**

1. Merge `box1-ops-contracts#3`.
2. Merge `box1-gitops#52`, then sync the `box1-kafka` Application, which has no automated sync.
3. Install the chosen secrets operator by GitOps PR (D-016).
4. Replace the inline Secret with the integration, and change the PostgreSQL role password.
5. Merge `box1-workloads-dev#50`. It can go earlier, since it is independent and adds the NetworkPolicy.
6. Merge `order-service#1`, which builds and promotes automatically.
7. Run the release reviewer pass and live acceptance. Record digest, revision and running pod. Then update the ledger and issue #11.

- Exact files to read: `checkpoint.md`, `decisions/D-016-secrets-integration-choice.md`, `requirements.yaml`, the prompt and profile from `box1-docs` `origin/main`.
- Blockers and required user decisions: D-016; every merge; the operator install.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#11
current_phase: 6
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
  implemented: 2
  locally_tested: 27
  ci_verified: 3
  deployed: 0
  live_verified: 0
  blocked: 2
  superseded: 1
image_digest: null
gitops_commit: null
review_passes_completed: [architecture, persistence, messaging, security, operations]
open_decisions: [D-016]
rollback_state: nothing deployed by this run
next_action: Get the user's answer to D-016, then open the operator install PR
```
