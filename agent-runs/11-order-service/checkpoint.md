# Checkpoint: box1-docs#11 Service 01, frontier profile

**Updated:** 2026-11-05 America/New_York
**Current phase:** 7, partially complete. The code is live, but acceptance is limited, the release smoke is at risk, and the Release pass has not run.
**Stop reason:** two cluster actions need approval. See the exact next action.

## Branches and PRs

| Repository | Branch | Head | PR | Checks |
|---|---|---|---|---|
| `order-service` | `order-domain` | `078f341` | [#1](https://github.com/box1-org/order-service/pull/1) | Pass |
| `box1-ops-contracts` | `order-service-v1-additions` | `7dcf290` | [#3](https://github.com/box1-org/box1-ops-contracts/pull/3) | None configured |
| `box1-gitops` | `order-dlq-topic` | `fe11b0f` | [#52](https://github.com/box1-org/box1-gitops/pull/52) | Pass |
| `box1-workloads-dev` | `order-service-runtime-config` | `de4a218` | [#50](https://github.com/box1-org/box1-workloads-dev/pull/50) | Pass |

All four are merged by the user. Deployed: digest `sha256:fb669bff…83fd`, source `749ef13`. New and open: `box1-templates#23` then `#24`, branches `onboarding-postgres-networkpolicy` and `workload-runtime-baseline`, porting #50 into the template.

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

- **Release pipeline failed.** `order-service-release-dq2fk` failed in promote at 09:15:01 EST, on the 300 s Argo wait. Argo is `OutOfSync` because `order-service-config-29d2hgcc29` requires pruning. Smoke was skipped, so it has not run against this image. The deployment is healthy at the expected revision. Tracked in box1-docs#42.
- **No dead-letter topic.** `box1-kafka` is `OutOfSync`, because `box1-gitops#52` is merged but not synced. A poison event could auto-create the topic with default retention. If that fails, the pod restarts.
- **Live database credential** (D-005, box1-docs#41). Specifics withheld, since this repository is public. The NetworkPolicy now limits access to it.
- Order data is readable on the LAN without credentials (box1-docs#40).
- The consumer path, outage handling and restart behavior are proven locally only.
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

The release with `gate` failed (`order-service-release-796ds`). See `evidence/08-security-availability.txt`. Two blockers need user approval: restore the NooBaa backing store, and give ACS access to the internal registry. Then re-trigger the release. `gate` is on `main`, so no `order-service` release can promote until both are fixed.
