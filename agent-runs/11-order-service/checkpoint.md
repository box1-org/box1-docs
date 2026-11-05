# Checkpoint: box1-docs#11 Service 01, frontier profile

**Updated:** 2026-11-05 America/New_York
**Current phase:** stopped at the entry to Phase 6. Phases 0 to 5 have exited, except the Release pass, which needs a deployment.
**Stop reason:** the next actions need approval (operator install, merges) and D-016 is open.

## Branches and PRs

| Repository | Branch | Head | PR | Checks |
|---|---|---|---|---|
| `order-service` | `order-domain` | `078f341` | [#1](https://github.com/box1-org/order-service/pull/1) | Pass |
| `box1-ops-contracts` | `order-service-v1-additions` | `7dcf290` | [#3](https://github.com/box1-org/box1-ops-contracts/pull/3) | None configured |
| `box1-gitops` | `order-dlq-topic` | `fe11b0f` | [#52](https://github.com/box1-org/box1-gitops/pull/52) | Pass |
| `box1-workloads-dev` | `order-service-runtime-config` | `de4a218` | [#50](https://github.com/box1-org/box1-workloads-dev/pull/50) | Pass |

Nothing is merged. Nothing changed on the cluster. The deployed service is still the scaffold.

Local paths: `order-service`, `run11-contracts`, `run11-workloads`, `run11-gitops`, `box1-docs-agent-run-11`.

## Test results

| Run | Result | Evidence |
|---|---|---|
| CI, `order-service-validate-vzxnp`, at `078f341` | 28 unit and contract tests, 5 integration tests, SpotBugs 0, Checkstyle 0 | `evidence/06-ci.txt` |
| Local with containers, at `078f341` | 64 and 8 tests, 0 failures, SpotBugs 0, Checkstyle 0 | `evidence/04-scenarios-local.txt` |
| Contracts, at `7dcf290` | `validate` pass, `test` 3 of 3. Drills 5 of 5 on the earlier commit. | `box1-ops-contracts#3` |
| Workstation load sample, at `764ada1` | About 276 MiB RSS, p95 11 ms at about 5 POST/s for 60 s | `evidence/05-resource-sample.txt` |

Local scenarios use `postgres:15-alpine` and `apache/kafka:4.2.0`. The deployed PostgreSQL is the Red Hat build, which needs a registry login to pull. The load sample predates the reviewer repairs.

## Ledger

27 `locally_tested`, 3 `ci_verified`, 2 `implemented`, 2 `blocked`, 1 `superseded`. None is `deployed` or `live_verified`.

## Reviewer passes

Architecture, persistence, messaging, security and operations are recorded in `review-findings/` with outcomes. The release pass has not run.

Open from review:

- A failed dead-letter send restarts the pod. Documented, not tested. Merge the topic first.
- Published outbox rows are never purged.
- Permanent publish errors retry forever.

## Open risks

- The live database credential (D-005, D-016). Specifics are withheld because this repository is public.
- Merging `order-service#1` deploys automatically, and unauthenticated order data then becomes reachable on the LAN (box1-docs#40).
- The release pipeline runs with `security-gates: disabled`.
- Failure scenarios do not run in CI. A later change could break them with CI still green.
- Smoke, Flyway with the deployed login and the `/tmp` limit are unproven against this image.
- The prompt still names `box1-ops-order` and `orders-service`.

## Resume notes

```sh
export DOCKER_HOST=unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')
export TESTCONTAINERS_RYUK_DISABLED=true
# Check the VM clock first. Host sleep leaves it behind, and Kafka then rejects messages.
podman machine ssh date; date -u
caffeinate -ims ./mvnw clean verify -Pcontainers -DskipITs=false
```

Re-verify the baseline before relying on it.

## Exact next action

Get the user's answer to D-016. If approved, open a `box1-gitops` PR installing the chosen operator, stating what merging deploys. Then follow the order in `handoff.md`.
