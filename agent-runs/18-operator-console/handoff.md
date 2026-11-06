# Handoff: box1-docs#18 operator console (frontier), stopped at Phase 6 for approvals

## Work completed
- **Service / platform workstream:** Service 08, web application / operator console.
- **Slice / requirements:** the whole prompt under `frontier`, up to delivery. Ledger: `requirements.yaml`.
- **Repository and branch:**
  - box1-org/operations-console `issue-18-console` @ `1d65b2b`.
  - box1-org/box1-gitops `run18-operations-console-keycloak` @ `16d561e`.
  - box1-org/box1-workloads-dev `run18-operations-console-runtime`.
- **Changed paths:**
  - operations-console:
    - `src/main/java/org/box1/console/**`
    - `src/main/resources/{application.properties,META-INF/openapi.yaml}`
    - `src/main/webui/**` (React/TS, lockfile)
    - `src/test/java/org/box1/console/**`
    - `src/test/e2e/**` (Playwright Firefox, local stack)
    - `pom.xml` (verified Node, frontend build)
    - `.tekton/release.yaml` (`security-gates: gate`, console-smoke)
    - `README.md`, `docs/{architecture,runbook,demo-walkthrough}.md`, `docs/screenshots/`
  - box1-gitops: `platform/identity/keycloak/realm/{operations-console-client.yaml,kustomization.yaml}`, README.
  - box1-workloads-dev: `workloads/operations-console/deployment.yaml` (env, replica comment).
- **PR / commit (actually created, none merged):**
  - operations-console#2.
  - box1-gitops#73.
  - box1-workloads-dev#90.
  - Probe operations-console#1 closed.

## Tests and deployment proof
- **Exact commands and observed results:**
  - `./mvnw -B -ntp verify -DskipITs=false`: 50 unit/HTTP + 5 IT, Checkstyle 0, SpotBugs/FindSecBugs 0.
  - `src/test/e2e` Playwright **Firefox** on the local stack: 15/15 (`evidence/03`, `evidence/04`).
- **CI status:**
  - Probe `operations-console-validate-zqk5s`.
  - Implementation `-l6jv2` (`d007f00`).
  - Repairs `-8pkct` (`1d65b2b`).
  - All Succeeded with the unchanged Golden Path task.
- **GitOps PR and deployed image digest:** none deployed. The deployed console is still the onboarding scaffold (`sha256:00c55736…`).
- **Routes / endpoints verified:** none for the console implementation. The upstreams' anonymous read behaviour was observed in discovery.

## Contract state
- **OpenAPI / event schemas changed:** new console contract `META-INF/openapi.yaml` 1.0.0, using #17's paths, Problem JSON and `sources`. No other service's contract was changed. No events.
- **Database migrations and forward compatibility:** none (stateless).
- **Consumer compatibility / pending follow-up:**
  - #17 can serve the same contract.
  - Offset paging over a moving window will need a cursor there.
  - `sources` vs `sourceStatus` naming is noted.

## Operations and safety
- **Secrets externalized / auth boundaries:**
  - No secrets. Public PKCE client with its own audience only.
  - Tokens stay in HttpOnly, Secure, SameSite=Strict encrypted cookies and are not forwarded to upstreams.
  - 401/403 Problem JSON; CSRF header, JSON and Origin checks.
  - CSP with one hashed stylesheet.
  - Session key is per pod (one replica).
- **Telemetry evidence:**
  - JSON logs with traceId; WARN line per failed upstream call.
  - `console_upstream_calls_total` and `console_upstream_duration`; bounded URI tags.
  - `traceparent` propagated. Export is off until #22.
- **Resource settings:** template 100m/256Mi request, 1/512Mi limit, 1 replica. The template pod measured 105 MiB; the console itself was not measured on the cluster.
- **Known risks and recovery/rollback:**
  - Revert the promotion commit in box1-workloads-dev (untested).
  - Merge order matters: #73 → roles → #90 → #2.
  - The first gated release could be blocked by RHACS findings.

## Next agent session
- **Next smallest slice:** after the approvals, Phase 6 delivery and then Phase 7 live acceptance on the Route (see `checkpoint.md`).
- **Exact files to read (not the whole repo):** `checkpoint.md`, `open-decisions.md`, `requirements.yaml`, operations-console `docs/runbook.md`.
- **Blockers and required user decisions:** O-1…O-9 in `open-decisions.md`, plus three merge approvals.
- **Context budget warning if near the 64K limit (`qwen-64k` only):** n/a.

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#18
current_phase: 6 (stopped at entry; merges need approval)
repositories:
  - name: box1-org/operations-console
    branch: issue-18-console
    commit: 1d65b2b
  - name: box1-org/box1-gitops
    branch: run18-operations-console-keycloak
    commit: 16d561e
  - name: box1-org/box1-workloads-dev
    branch: run18-operations-console-runtime
    commit: see PR #90
  - name: box1-org/box1-docs
    branch: agent-run/18-operator-console
    commit: (this commit)
run_state_path: agent-runs/18-operator-console/
requirements:
  proposed: 1
  implemented: 3
  locally_tested: 19
  ci_verified: 12
  deployed: 0
  live_verified: 0
  blocked: 1
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [architecture, persistence, messaging, security, operations, release, frontend]
open_decisions: [O-1 order-fulfillment link, O-2 asset-service azp, O-3 session key secret, O-4 favicon, O-5 customer role, O-6 cluster fixtures, O-7 Keycloak merge + role assignment, O-8 no held ERP on cluster, O-9 upstream token strategy]
rollback_state: nothing deployed; all changes are unmerged PRs
next_action: user approves merges in order box1-gitops#73 -> assign roles -> box1-workloads-dev#90 -> operations-console#2; then Phase 6 observation and Phase 7 live acceptance
```
