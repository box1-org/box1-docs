# Agent handoff: deployed, live acceptance awaiting approval

## Work completed
- Service / platform workstream: Service 02, Inventory service (box1-docs#12), `frontier` profile.
- Slice / requirements: the whole issue, deployed. Live acceptance is partial: the live order needs approval.
- Repository and branch: see `checkpoint.md`.
- Changed paths: `inventory-service`: `src/main/java/org/box1/inventory/`, `src/main/resources/db/migration/`, `src/main/resources/application.properties`, `src/test/java/org/box1/inventory/`, `docs/`, `README.md`, `mkdocs.yml`, `pom.xml`, `.tekton/release.yaml`. Contracts: `openapi/inventory-service.yaml`, `INVENTORY-RESERVATIONS.md`, `TOPICS.md`, `postgres/OWNERSHIP.md`, `postgres/migrations/inventory/`, `scripts/validate.mjs`, `test/`. GitOps: `platform/kafka/`. Workloads: `workloads/inventory-service/deployment.yaml`.
- PR / commit: [inventory-service#1](https://github.com/box1-org/inventory-service/pull/1), [box1-ops-contracts#5](https://github.com/box1-org/box1-ops-contracts/pull/5), [box1-gitops#57](https://github.com/box1-org/box1-gitops/pull/57), [box1-workloads-dev#57](https://github.com/box1-org/box1-workloads-dev/pull/57). All four merged by the agent with the user's approval, plus the pipeline's promotion `box1-workloads-dev#58`.

## Tests and deployment proof
- Exact commands and observed results: `./mvnw clean verify -Pcontainers -DskipITs=false` at `5bd69c7`: 71 + 10 tests, 0 failures, SpotBugs 0, Checkstyle 0. Local saga with real order-service main: 23 of 23.
- CI status: `inventory-service-validate` pass at `5bd69c7`.
- GitOps PR and deployed image digest: `box1-workloads-dev#58` (`cd0c280`), `sha256:d21ab42b4822428d0b6c1404261297bf03027701145f1486f78b6f447fd34531`. The pod's imageID matches. The gate passed.
- Routes / endpoints verified: `/api/info` gitRef `6b722a3`, reads by site, 400 and 404 Problems, readiness, OpenAPI. Mutations rejected by `inventory-api-smoke`. See `evidence/08-release-live.txt`.

## Contract state
- OpenAPI / event schemas changed: inventory OpenAPI added, states and reason codes documented, two `TOPICS.md` rows. Event schemas unchanged.
- Database migrations and forward compatibility: `V1` schema, `V2` lab fixture. Applied live by Flyway at deploy. Forward-only.
- Consumer compatibility / pending follow-up: checked against the real order-service main locally. Release has no contract event (follow-up).

## Operations and safety
- Secrets externalized / auth boundaries: datasource from Secret reference. `/internal` needs a Keycloak role that no client has yet (D-010). Reads default to `authenticated` (D-011).
- Telemetry evidence: local only, from logs and `/q/metrics`. No trace backend.
- Resource settings: unchanged at 100m/256Mi requests and 1/512Mi limits. Workstation sample 242 MiB RSS at 256 MiB heap.
- Known risks and recovery/rollback: see `checkpoint.md`. Rollback is a revert of #58, which restores the scaffold digest. The tables and offsets stay. Not exercised.

## Next agent session
- Next smallest slice: the approved live order, per `checkpoint.md`.
- Exact files to read: `checkpoint.md`, `decisions/D-002`, `D-010`, `D-011`, `requirements.yaml`, the service's `docs/runbook.md`.
- Blockers and required user decisions: approval for the live order. D-010 stays closed by the agent's choice.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#12
current_phase: 7
repositories:
  - name: inventory-service
    branch: inventory-domain
    commit: 5bd69c759ff2d3821caf4839ac772041b9b6a09e
  - name: box1-ops-contracts
    branch: inventory-service-v1
    commit: 85d72e3cce2f1928ea60d3e6b3f73b313a5828fe
  - name: box1-gitops
    branch: inventory-dlq-topic
    commit: f34d95877f35afaf872d7708570411fbfa0a79e8
  - name: box1-workloads-dev
    branch: inventory-service-runtime-config
    commit: c13293be1d345b323b7ee5936b365b2190bbab91
run_state_path: agent-runs/12-inventory-service/
requirements:
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 1
  deployed: 25
  live_verified: 8
  blocked: 1
  superseded: 0
image_digest: sha256:d21ab42b4822428d0b6c1404261297bf03027701145f1486f78b6f447fd34531
gitops_commit: cd0c28024c6f1f5f3e65c125bfbf158a9cd998a7
review_passes_completed: [architecture, persistence, messaging, security, operations, release]
open_decisions: [live acceptance order approval]
rollback_state: revert box1-workloads-dev#58 restores scaffold 4a1ae810; not exercised; V1 and V2 stay applied
next_action: User approves one live order through the Order Route, then verify per checkpoint.md
```
