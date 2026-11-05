# Checkpoint: box1-docs#11 Service 01, frontier profile

**Updated:** 2026-11-05 America/New_York
**Current phase:** 7. The code is live and the Release pass ran. Acceptance is partial.
**Stop reason:** the release from `order-service#4` did not start. See the exact next action.

## Branches and PRs

| Repository | Branch | Head | PR | Checks |
|---|---|---|---|---|
| `order-service` | `order-domain` | `078f341` | [#1](https://github.com/box1-org/order-service/pull/1) | Pass |
| `box1-ops-contracts` | `order-service-v1-additions` | `7dcf290` | [#3](https://github.com/box1-org/box1-ops-contracts/pull/3) | None configured |
| `box1-gitops` | `order-dlq-topic` | `fe11b0f` | [#52](https://github.com/box1-org/box1-gitops/pull/52) | Pass |
| `box1-workloads-dev` | `order-service-runtime-config` | `de4a218` | [#50](https://github.com/box1-org/box1-workloads-dev/pull/50) | Pass |

All four are merged by the user. Also merged by the user: `order-service#2`, `#3`, `box1-gitops#53`, `#54`, `#55`. Promotion: `box1-workloads-dev#52`, merged by the pipeline. Deployed: digest `sha256:513c366d…b65d`, source `4ec33fb`. Also merged: `box1-templates#23`, `#24`, `#25`. Open: `order-service#4`. Template branches were branches `onboarding-postgres-networkpolicy` and `workload-runtime-baseline`, porting #50 into the template.

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

11 `live_verified`, 22 `deployed`, 1 `blocked`, 1 `superseded`. See `requirements.yaml`.

## Reviewer passes

All six are recorded in `review-findings/` with outcomes. The Release pass verdict is conditional.

Open from review:

- A failed dead-letter send restarts the pod. Documented, not tested. Merge the topic first.
- Published outbox rows are never purged.
- Permanent publish errors retry forever.

## Open risks

- **Rollback restores a failing image.** Reverting the promotion deploys `fb669bff`, which has 14 `FAIL_BUILD` violations. Not exercised. Prefer rolling forward.
- **The gate can be bypassed, and its results are not kept per run** (box1-docs#42).
- **Registry TLS verification is off** (box1-docs#44).
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

`order-service#4` is merged but not deployed. `order-service-release-9kb6b` never started, because Pipelines as Code got a 404 from GitHub, and `/retest` also failed. See `evidence/09-release.txt`.

Waiting on the user, each needing their approval:

1. Cancel the orphaned `order-service-release-9kb6b`. The permission layer denied this for the agent.
2. Push a new commit to `order-service` `main`, or approve the agent doing it, to start a release.
3. Merge `box1-ops-contracts#4` (timeline `sequence` is global, decided by the user).

Then confirm `order-api-smoke`, the served OpenAPI and a relative `Location`, update the ledger and close box1-docs#11. The user asked to close it. Its follow-ups are box1-docs#40, #41, #42, #43, #44.
