# Checkpoint: box1-docs#15, frontier

**Current phase:** 3 complete; Phase 4 (verification scenarios) in progress.
**Updated:** 2026-11-05 ~19:00 EST.

## Branches and commits
| Repo | Branch | Commit | Worktree |
|---|---|---|---|
| asset-service | telemetry-service | 18dddb0 | ../run15-asset-service (clone) |
| box1-ops-contracts | asset-service-v1 | 8764f7d | ../run15-contracts |
| box1-workloads-dev | asset-service-runtime-config | uncommitted edits | ../run15-workloads |
| box1-gitops | telemetry-dlq-topic | 8bca2c0 | ../run15-gitops |
| box1-gitops | asset-service-keycloak-client | 95206e7 | ../run15-gitops (current branch) |
| box1-docs | agent-run/15-telemetry-service | this commit | ../run15-docs |

## Tests
- `./mvnw verify` (no containers) and `./mvnw test -Pcontainers`: 50 tests, 0 failures at d5646c2; verify passes static analysis at 18dddb0. Evidence `evidence/03-tests-local.txt`.
- Contracts: `npm test` 5/5, `npm run validate` 10 fixtures, 11 schemas, 18 examples.

## Local environment (for Phase 4)
- Containers `run15-pg` :15432, `run15-kafka` :19092, `run15-keycloak` :18180 (realm built from the proposed KeycloakClient; users and local-only passwords in the session scratch directory, never published).
- App: scratch `run-local.sh` on :18080, `POD_NAMESPACE=run15-local`, chaos allowlisted for `run15-local` only.
- E2E client: scratch `e2e/console_client.py` (real code-flow login).

## Open decisions (report together at the next stop)
- D-012 DLQ topic merge + box1-kafka selective sync (approval).
- D-013 Keycloak client merge (approval); who drives live console runs.
- D-014 database Secret: recommended out-of-band Secret, no password in Git.
- D-015 chaos namespace name.
- D-016 brand mark asset (console uses a text wordmark until answered).
- Private discovery findings: reported directly to the user; not recorded here.

## Exact next action
Run Phase 4 scenarios against the local jar: seed replay via session, TTL with no client, stop-all mid-run, kill -9 restart mid-run, anonymous and no-role, non-allowlisted namespace, broker pause (podman pause run15-kafka) and producer-pause chaos, caps via direct API, invalid/oversize, axe scan and keyboard-only with headless Firefox, screenshots. Then commit workloads branch and open PRs.
