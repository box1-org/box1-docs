# Checkpoint: box1-docs#11 Service 01, frontier profile

**Updated:** 2026-11-05 America/New_York
**Current phase:** 7. The code is live and the Release pass ran. Acceptance is partial.
**Stop reason:** the release is live. Remaining decisions are the user's. See the exact next action.

## Branches and PRs

| Repository | Branch | Head | PR | Checks |
|---|---|---|---|---|
| `order-service` | `order-domain` | `078f341` | [#1](https://github.com/box1-org/order-service/pull/1) | Pass |
| `box1-ops-contracts` | `order-service-v1-additions` | `7dcf290` | [#3](https://github.com/box1-org/box1-ops-contracts/pull/3) | None configured |
| `box1-gitops` | `order-dlq-topic` | `fe11b0f` | [#52](https://github.com/box1-org/box1-gitops/pull/52) | Pass |
| `box1-workloads-dev` | `order-service-runtime-config` | `de4a218` | [#50](https://github.com/box1-org/box1-workloads-dev/pull/50) | Pass |

All four are merged by the user. Also merged by the user: `order-service#2`, `#3`, `box1-gitops#53`, `#54`, `#55`. Promotion: `box1-workloads-dev#52`, merged by the pipeline. Deployed: digest `sha256:513c366d…b65d`, source `4ec33fb`. New and open: `box1-templates#25`, plus `#23` then `#24`, branches `onboarding-postgres-networkpolicy` and `workload-runtime-baseline`, porting #50 into the template.

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
- **The gate has not shown a rejection,** and it can be bypassed. See `review-findings/release.md`.
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

The release passed with `gate`: `order-service-release-jn4rl`, source `4ec33fb`, digest `sha256:513c366d...b65d`, GitOps `9293ad8`. See `evidence/09-release.txt` and `review-findings/release.md`.

Waiting on the user:

1. Approve or decline a controlled negative test of the gate, which has never rejected an image through the Task.
2. Decide on the open findings: served OpenAPI, smoke coverage, `Location` scheme, timeline `sequence`, gate bypass.
3. Merge `box1-templates#25`, #23 and #24.

Acceptance stays partial. `ORD-LIVE-LIFECYCLE` is blocked, and consumer, outage and restart behavior are proven locally only.
