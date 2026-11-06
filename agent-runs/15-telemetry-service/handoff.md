# Agent handoff: delivered and verified live; console run with the user next

## Work completed
- Service / platform workstream: Service 05, asset telemetry service, box1-docs#15, `frontier` profile.
- Slice / requirements: the whole issue, delivered to `asset-service-dev`. Live acceptance is partial: the seeded load run waits for the user to drive the console, and the chaos run is blocked by D-015, which the user deferred.
- Repository and branch: `box1-org/asset-service` main at 1706dd0b (merged from `telemetry-service`). Changed paths are the same as in the earlier handoff; see git history.
- PR / commit, all merged with the user's approval:

| PR | Merge commit |
|---|---|
| box1-gitops#62 (DLQ topic) | 169dda0c |
| box1-gitops#63 (Keycloak client) | 39e2e8fe |
| box1-workloads-dev#64 (database, runtime config) | 5ec7bf5d |
| box1-ops-contracts#7 | d57a4efb |
| asset-service#1 | 1706dd0b |
| box1-workloads-dev#72 (promotion, merged automatically) | 7a90162e |

## Tests and deployment proof
- Exact commands and observed results:
  - `./mvnw clean verify -Pcontainers`: 62 tests, 0 failures.
  - CI `-DskipITs=false`: 45 + 5 tests, 0 failures.
  - Local scenarios and browser checks pass. Evidence in `evidence/04`, `07` and `09`.
- CI status: asset-service-validate at 490a7e2 succeeded. Release asset-service-release-rmcdq succeeded on its first run: gate policy pass, promote, smoke.
- GitOps PR and deployed image digest: #72, revision 7a90162e, digest `sha256:6d8e8c172b2885f35a551eb34c53429e1ac85a1771263ba841795c683fbde944`. The pod imageID matches, and Argo is Synced/Healthy.
- Routes / endpoints verified (anonymous, read-only):
  - `/api/info` gitRef is 1706dd0b.
  - Readiness is UP: database, messaging, projection.
  - The data API returns 401, control returns 499 or 302, and the console redirects to `https`.
  - Security headers are present.
  - The Release pass agrees (`review-findings/release.md`).

## Contract state
- OpenAPI / event schemas changed: `equipment.threshold-exceeded.v1` and `openapi/asset-service.yaml` are on main. The served OpenAPI is less specific than the contract for the two reads (REL-2, follow-up).
- Database migrations and forward compatibility: V1 applied on the cluster. Forward-only.
- Consumer compatibility / pending follow-up: no consumers yet.

## Operations and safety
- Secrets externalized / auth boundaries:
  - **Database:** the Secret was created out of band by the user, and no password is in Git.
  - **Keycloak client:** public client with PKCE; roles `chaos-operator`, `telemetry-writer` and `telemetry-reader`, assigned to no one yet.
  - **Chaos:** off (D-015 deferred). Load control is on in dev.
- Telemetry evidence: `asset_*` metrics are on `/q/metrics`. Trace export is off (#22). OpenTelemetry logs a "VertxTracer delegate not set" warning per request: log noise, follow-up.
- Resource settings:
  - App: 100m/320Mi requests, 1/512Mi limits.
  - PostgreSQL: 50m/128Mi requests on a 5Gi PVC.
- Known risks and recovery/rollback:
  - **Rollback:** revert 7a90162e to restore the scaffold digest `sha256:0dc4185e…`, whose image still exists. Not exercised.
  - **Sessions:** they end on restart. Keep one replica.

## Next agent session
- Next smallest slice: after the user's console load run, record its evidence: run ID, seed, digest, audit, and the pod log lines. Then update TEL-LIVE-001.
- Exact files to read: `checkpoint.md`, `requirements.yaml`, `evidence/10-delivery.txt`, `decisions/D-015`.
- Blockers and required user decisions:
  - The user assigns `chaos-operator` and runs the console.
  - D-015, for any chaos run.
- Follow-ups for the backlog:
  - REL-2: OpenAPI scopes for the reads.
  - VertxTracer log noise.
  - ARCH-10: machine client for `telemetry-writer` (needs approval).
  - SEC-5: Secret-backed session key (needs approval).
  - OPS-11: catch-up memory measurement.
  - MDC trace IDs on run threads.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#15
current_phase: 7 (waiting for the user-driven console run)
repositories:
  - name: asset-service
    branch: main
    commit: 1706dd0b0123cbddd510d1fb6bf9d44cc020fee5
  - name: box1-ops-contracts
    branch: main
    commit: d57a4efb190a35fea627052c81e626c3d1d8db48
  - name: box1-workloads-dev
    branch: main
    commit: 7a90162e4ed31aba2fa9e98e07bc765d321c30d9
  - name: box1-gitops
    branch: main
    commit: 39e2e8fe62ead776f446ecea6bb7009f45b650c1
run_state_path: agent-runs/15-telemetry-service/
requirements:
  proposed: 1
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 26
  live_verified: 5
  blocked: 0
  superseded: 0
image_digest: sha256:6d8e8c172b2885f35a551eb34c53429e1ac85a1771263ba841795c683fbde944
gitops_commit: 7a90162e4ed31aba2fa9e98e07bc765d321c30d9
review_passes_completed: [architecture, persistence, messaging, security, operations, release]
open_decisions: [user console load run, D-015 chaos namespace (deferred)]
rollback_state: revert 7a90162e restores sha256:0dc4185e (image present); not exercised; tables, PVC, topic and client stay
next_action: user assigns chaos-operator and runs one seeded load run in the console; agent then records evidence read-only
```
