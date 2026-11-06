# Agent handoff: delivered, live load run verified; chaos deferred

## Work completed
- Service / platform workstream: Service 05, asset telemetry service, box1-docs#15, `frontier` profile.
- Slice / requirements: the whole issue, delivered to `asset-service-dev`. Live acceptance is partial. The seeded load run is done and verified on the cluster (`evidence/11`: run_b63ce49d56084ec0b32a, digest matches an independent prediction). The chaos run is blocked by D-015, which the user deferred.
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
| asset-service#2 (CORS fix, merged by the user) | 828065e1 |
| box1-workloads-dev#74 (promotion, merged automatically) | aa0b4b04 |

## Tests and deployment proof
- Exact commands and observed results:
  - `./mvnw clean verify -Pcontainers`: 62 tests, 0 failures.
  - CI `-DskipITs=false`: 45 + 5 tests, 0 failures.
  - Local scenarios and browser checks pass. Evidence in `evidence/04`, `07` and `09`.
- CI status: asset-service-validate at 490a7e2 succeeded. Release asset-service-release-rmcdq succeeded on its first run: gate policy pass, promote, smoke.
- GitOps PR and deployed image digest: #72, revision 7a90162e, digest `sha256:4d8623986033b87bea25bed9461f0731e6616f47de00cc1bf21132dbbf0675d0`. The pod imageID matches, and Argo is Synced/Healthy.
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
current_phase: 7 (load half done; chaos half blocked by D-015)
repositories:
  - name: asset-service
    branch: main
    commit: 828065e16c67ddbe980f591dc8c3beac8df1e300
  - name: box1-ops-contracts
    branch: main
    commit: d57a4efb190a35fea627052c81e626c3d1d8db48
  - name: box1-workloads-dev
    branch: main
    commit: aa0b4b044d96ce42a26e0119d2823c6591811250
  - name: box1-gitops
    branch: main
    commit: 39e2e8fe62ead776f446ecea6bb7009f45b650c1
run_state_path: agent-runs/15-telemetry-service/
requirements:
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 20
  live_verified: 11
  blocked: 1
  superseded: 0
image_digest: sha256:4d8623986033b87bea25bed9461f0731e6616f47de00cc1bf21132dbbf0675d0
gitops_commit: aa0b4b044d96ce42a26e0119d2823c6591811250
review_passes_completed: [architecture, persistence, messaging, security, operations, release]
open_decisions: [D-015 chaos namespace (deferred by the user)]
rollback_state: revert 7a90162e restores sha256:0dc4185e (image present); not exercised; tables, PVC, topic and client stay
next_action: when the user names a chaos namespace (D-015), a workloads PR enables chaos there; then one seeded chaos run with alert and clear evidence
```
