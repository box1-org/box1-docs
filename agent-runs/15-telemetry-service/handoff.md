# Agent handoff: implemented and reviewed, stopped before delivery

## Work completed
- Service / platform workstream: Service 05, the asset telemetry service, box1-docs#15, `frontier` profile.
- Slice / requirements: the whole issue, through Phase 5. Phases 6 and 7 need approvals and user decisions (D-012 to D-016).
- Repository and branch: `box1-org/asset-service` `telemetry-service` (the user named this repository; D-001). Other repositories are listed in the table below.
- Changed paths: `src/main/java/org/box1/asset/**`, `src/main/resources/application.properties`, `src/main/resources/db/migration/V1__telemetry_schema.sql`, `src/main/resources/META-INF/resources/{console/,signed-out.html}`, `src/test/java/org/box1/asset/**`, `README.md`, `docs/{architecture,runbook,index}.md`, `mkdocs.yml`, `pom.xml`, `.tekton/release.yaml`.
  - Contracts: `events/v1/equipment.threshold-exceeded.schema.json`, `fixtures/events.json`, `TELEMETRY.md`, `TOPICS.md`, `postgres/OWNERSHIP.md`, `openapi/asset-service.yaml`, `scripts/validate.mjs`, `test/contracts.test.mjs`.
  - GitOps: `platform/kafka/topics/telemetry-dlq.yaml` and its kustomization; `platform/identity/keycloak/realm/asset-service-client.yaml` and its kustomization.
  - Workloads: `workloads/asset-service/{postgres.yaml,deployment.yaml,kustomization.yaml}`.
- PR / commit, all open and none merged:

| PR | Head | What merging deploys |
|---|---|---|
| [box1-gitops#62](https://github.com/box1-org/box1-gitops/pull/62) | 8bca2c0 | Nothing until a selective `box1-kafka` sync, which needs its own approval |
| [box1-gitops#63](https://github.com/box1-org/box1-gitops/pull/63) | b313754 | Client `asset-service` and the roles `chaos-operator`, `telemetry-writer`, `telemetry-reader`, in the live realm (automated sync) |
| [box1-workloads-dev#64](https://github.com/box1-org/box1-workloads-dev/pull/64) | bb0bcae | PostgreSQL, PVC, NetworkPolicy and Deployment `env`. The Secret must exist first |
| [box1-ops-contracts#7](https://github.com/box1-org/box1-ops-contracts/pull/7) | 2fe191d | Nothing. The service pins this commit |
| [asset-service#1](https://github.com/box1-org/asset-service/pull/1) | 11fa5a1 | The release: build, `gate`, promotion, smoke into `asset-service-dev` |

## Tests and deployment proof
- Exact commands and observed results:
  - `./mvnw clean verify -Pcontainers` at 742f9d7: 62 tests, 0 failures, Checkstyle 0, SpotBugs 0.
  - `./mvnw -B clean verify -DskipITs=false` at 11fa5a1: 45 tests and 5 integration tests, 0 failures.
  - Phase 4 scenarios and the post-review reruns all pass locally. They cover the 13 prompt scenarios plus burst cap and database outage. Evidence in `evidence/04` and `evidence/07`.
  - Headless Firefox: axe WCAG 2.1 AA clean at 1440 and 390 px, keyboard-only flow, honest UNKNOWN state. Evidence in `evidence/05`, screenshots in `evidence/screenshots/`.
- CI status: asset-service-validate-zr7tn at 11fa5a1 succeeded (`evidence/08`). The gitops and workloads PR checks pass.
- GitOps PR and deployed image digest: none. Nothing has been merged or deployed. The cluster still runs the scaffold `sha256:0dc4185e…`.
- Routes / endpoints verified: none on the cluster for this change. Read-only discovery of the scaffold's Route only (`evidence/01`).

## Contract state
- OpenAPI / event schemas changed:
  - New `equipment.threshold-exceeded.v1`, an additive v1 change.
  - New `openapi/asset-service.yaml`.
  - `TELEMETRY.md` covers keying, ordering, the deterministic reading eventId, first-value-wins and the DLQ.
  - `equipment.reading.v1` is unchanged.
- Database migrations and forward compatibility: one forward-only `V1` that has never been applied anywhere shared. Earlier images do not use the database.
- Consumer compatibility / pending follow-up: there are no consumers today. A clear or escalation event would be an additive v1 type.

## Operations and safety
- Secrets externalized / auth boundaries:
  - **Database:** no password in Git. The Secret is created out of band per D-014, which is open.
  - **Keycloak client:** public, PKCE, no secret.
  - **Data API:** bearer-only; anonymous requests get 401.
  - **Console:** code flow with `chaos-operator`. Tokens must carry `azp=asset-service`.
  - **Golden Path smoke paths:** unchanged and public.
  - **Chaos:** off. Load control is on in dev only.
- Telemetry evidence: metrics and readouts were exercised locally. Trace export stays off until #22. MDC trace IDs on run threads were not verified.
- Resource settings:
  - App: 100m/320Mi requests, 1/512Mi limits. RSS measured 213–232 MiB at 50 readings/s.
  - PostgreSQL: 50m/128Mi requests on a 5Gi PVC.
  - Catch-up memory was not measured.
- Known risks and recovery/rollback:
  - **Cluster login is not established.** It was verified only against local Keycloak 26.4; the cluster runs RH-SSO 7.6.
  - **The `gate` policy result for this image is unknown.**
  - **Sessions end on restart.** Keep one replica.
  - **Rollback:** revert the promotion commit in `box1-workloads-dev`. The tables stay.

## Next agent session
- Next smallest slice: the approved delivery sequence in `checkpoint.md`, then Phase 7: one seeded load run and one chaos run on the cluster, with audit, alert and clear evidence.
- Exact files to read: `checkpoint.md`, `decisions/D-012` to `D-016`, `requirements.yaml`, and the asset-service `docs/runbook.md` ("First deployment order" and its preflight).
- Blockers and required user decisions: D-012 to D-016, and approval for each merge, each sync and each live run.
- Context budget warning: not applicable (`frontier`).

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#15
current_phase: 6 (stopped at entry)
repositories:
  - name: asset-service
    branch: telemetry-service
    commit: 11fa5a1055439eb4ce01018c836d5f5d4c28b848
  - name: box1-ops-contracts
    branch: asset-service-v1
    commit: 2fe191dc7587be4c17e0c672af6e324e995aab57
  - name: box1-workloads-dev
    branch: asset-service-runtime-config
    commit: bb0bcae
  - name: box1-gitops
    branch: telemetry-dlq-topic
    commit: 8bca2c0
  - name: box1-gitops
    branch: asset-service-keycloak-client
    commit: b313754
run_state_path: agent-runs/15-telemetry-service/
requirements:
  proposed: 2
  implemented: 1
  locally_tested: 19
  ci_verified: 10
  deployed: 0
  live_verified: 0
  blocked: 0
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [architecture, persistence, messaging, security, operations]
open_decisions: [D-012 DLQ merge and sync, D-013 Keycloak client merge, role assignment and live driver, D-014 database credential, D-015 chaos namespace, D-016 brand mark]
rollback_state: nothing merged; cluster unchanged (scaffold digest sha256:0dc4185e…)
next_action: user approves D-012 (merge box1-gitops#62), then each step in checkpoint.md in order
```
