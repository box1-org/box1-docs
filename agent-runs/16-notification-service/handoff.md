# Agent handoff — box1-docs#16 notification service (frontier)

## Work completed
- **Service / platform workstream:** Service 06, the notification service (operator notices).
- **Slice / requirements:** this service's whole vertical slice through Phase 5. Phases 6–7 are stopped for approvals.
- **Repository and branch:** box1-org/notification-service `issue-16-notification` at `8b8c27698760ebbc91e50ea86ea91507ded1cdad`.
- **Changed paths:**
  - `pom.xml`;
  - `src/main/java/org/box1/notification/**`;
  - `GreetingResource`/`InfoResource` (`@PermitAll`);
  - `src/main/resources/application.properties`;
  - `db/migration/V1__notification_schema.sql`;
  - `src/test/java/org/box1/notification/**`;
  - `README.md`, `docs/architecture.md`, `docs/runbook.md`, `docs/index.md`, `mkdocs.yml`.
- **PRs (none merged):**
  - notification-service#1;
  - box1-ops-contracts#9;
  - box1-gitops#75 (DLQ topic);
  - box1-gitops#76 (Keycloak client);
  - box1-workloads-dev#94 (PostgreSQL, env).

## Tests and deployment proof
- **Commands and results:**
  - `./mvnw -B -ntp verify -Pcontainers -DskipITs=false` on `8b8c276`: Surefire 57/57 and Failsafe 7/7 passed; 0 Checkstyle; 0 SpotBugs (`evidence/05-review-repairs.md`).
  - Scenario map: `evidence/03-local-tests.md`.
- **CI:** `box1-ci/notification-service-validate-7gp7r` Succeeded on `8b8c276` (38 + 5; container tests are excluded in CI).
- **GitOps PR and deployed digest:** promotion box1-workloads-dev#108; deployed `sha256:69788422…` from `bacc353`, Argo Synced/Healthy at `2c8f93c` (`evidence/07-live.md`).
- **Routes / endpoints verified:**
  - release smoke checks by hand;
  - 401 for anonymous and invalid tokens;
  - reader and console reads 200;
  - console fault control 403;
  - one real order (REJECTED) gave one notice, delivered on attempt 3 after two stub 503s;
  - no customer ID in the API response, pod log or event (`evidence/09-live-acceptance.md`).

## Contract state
- **OpenAPI / event schemas changed:**
  - `notification.delivered.v1` and `notification.failed.v1` (box1-ops-contracts#9);
  - `TOPICS.md` `notification` group on the order topic;
  - served OpenAPI `/q/openapi`.
- **Database migrations:** Flyway V1 creates new tables only; rollback is digest revert.
- **Consumer compatibility / follow-up:**
  - `contracts.ref` must be repinned after #9 merges.
  - The `box1.notification.dlq.v1` row in `TOPICS.md` is open (O-1).

## Operations and safety
- **Secrets and auth boundaries:**
  - No secret in Git. The DB credential is a user-created Secret, used through `secretKeyRef`.
  - Keycloak public PKCE client; `azp`-scoped roles; ID tokens refused.
  - Fault control is off, with an empty allowlist.
- **Telemetry:**
  - JSON logs with MDC.
  - Consume and deliver spans are parented on the envelope `traceparent`; export is off (#22).
  - `box1_notification_*` metrics, including pending age, attempts, delivered, failed by category and snapshot age.
- **Resources:**
  - App: 100m/256Mi requests, 1 CPU/512Mi limits. Not measured live; Phase 7.
  - PostgreSQL: 50m/128Mi, 1 Gi PVC.
- **Known risks and recovery:**
  - The release order is mandatory (O-6).
  - The DLQ keeps a poisoned `order.placed.v1` for 14 days (O-7).
  - The floor value needs a decision (O-8).
  - The audit trigger can be dropped by the table owner (lab limit, #41).
  - Rollback is a Git revert of the promotion; untested.

## Next agent session
- **Next smallest slice:** follow-ups in checkpoint.md (audit `actor_subject` in the API is the smallest).
- **Exact files to read:**
  - checkpoint.md, open-decisions.md, D-014;
  - notification-service `docs/runbook.md`;
  - box1-workloads-dev#94.
- **Blockers and required user decisions:** none.

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#16
current_phase: "7 complete for cluster-provable requirements"
repositories:
  - name: box1-org/notification-service
    branch: issue-16-notification
    commit: 8b8c27698760ebbc91e50ea86ea91507ded1cdad
  - name: box1-org/box1-ops-contracts
    branch: notification-events-v1
    commit: 1078fd4
  - name: box1-org/box1-gitops
    branch: run16-notification-dlq / run16-notification-keycloak
    commit: 37b9a0d / f40d9ca
  - name: box1-org/box1-workloads-dev
    branch: run16-notification-runtime
    commit: 16c05a8
  - name: box1-org/box1-docs
    branch: agent-run/16-notification-service
    commit: (this commit)
run_state_path: agent-runs/16-notification-service/
requirements:
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 13
  live_verified: 8
  blocked: 0
  superseded: 0
image_digest: sha256:69788422d2f3beef94a255e4247ba3142f662f9edb25018489f2058edd5b363a
gitops_commit: box1-workloads-dev ef17294 (promotion #108 1d54764)
review_passes_completed: [architecture, persistence, messaging, security, operations, release]
open_decisions: []
rollback_state: "Revert promotion #108 (and #110/#94 if needed) in box1-workloads-dev to return to template digest sha256:abc6446a…b582; untested"
next_action: "None; follow-ups in checkpoint.md"
```
