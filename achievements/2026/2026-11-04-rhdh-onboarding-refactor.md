# RHDH onboarding refactor: phased delivery and live validation

**Date:** 2026-11-04 to 2026-11-05 (America/New_York)
**Status:** Partially complete. The phased workflow is deployed and has completed live onboarding runs. Failure-path work and timing analysis remain open in [box1-docs#32](https://github.com/box1-org/box1-docs/issues/32).

## Outcome

New Quarkus services now onboard through Developer Hub in separate phases. The first build starts once its own prerequisites exist, and the first rollout starts within seconds of the promotion PR merging.

On the final live run, `enterprise` went from request to verified deployment in 200 seconds. The image build was the largest single step at 90 seconds (45%). This is one run, so **no general performance improvement is established**.

The refactor kept the existing delivery model: two GitOps PRs, immutable digest promotion, Argo as the deployment mechanism, exact-head PR validation, ownership markers, the per-service Lease, and temporary credential cleanup. No CRD or controller was added, and Tekton gained no deployment responsibility.

## Starting baseline

`box1:development:onboard` was one long action covering the GitOps PRs, Argo sync, platform readiness, the first build, promotion, and verification. Retries and progress were hard to follow, and the build waited on platform checks it did not need.

PR [box1-templates#9](https://github.com/box1-org/box1-templates/pull/9) had already extracted phase actions, but a code review on 2026-11-04 found the work unfinished:

- **Parallel waits conflicted.** The wrapper started waits that wrote state with the same `resourceVersion`. A fake API enforcing `resourceVersion` reproduced the conflict.
- **The earlier build start did not reach template runs.** The template ran the full platform checks before the build.
- **The wrapper had its own orchestration path**, separate from the template's.
- **Explicit Argo syncs were effectively unreachable.** The wait before each request finished only once the Application was already Synced and Healthy, and a test mock hid this.
- **Nothing requested a sync after the promotion merge.**

Earlier runs on older plugin versions took 638 to 699 seconds when auto-sync performed the rollout (`voyager`, `gold-service`, `ds9`). These are not a controlled baseline. No timing dataset from before the refactor is available.

## What changed

| PR | Change |
| --- | --- |
| [box1-templates#13](https://github.com/box1-org/box1-templates/pull/13), [box1-gitops#42](https://github.com/box1-org/box1-gitops/pull/42) | Serialized state writes and shared Lease renewals. Moved the build start to its dependency boundary. Made the wrapper run the same phases as the template. Required platform readiness before promotion. Made the explicit sync request reachable. Fixed a stale Kafka artifact name in `validate.mjs`. |
| [box1-templates#14](https://github.com/box1-org/box1-templates/pull/14), [box1-gitops#43](https://github.com/box1-org/box1-gitops/pull/43) | `promote` requests an Argo sync to the merge commit and records it, so a retry does not repeat it. `verify` fails at once if that sync fails. |

**Decision: the build stays one action.** The handoff suggested `build:start` and `build:wait` as an option. Scaffolder steps run one at a time, so overlap across steps would leave the credential Secret alive between them if a task died. The overlap instead runs inside `box1:development:build`, which the handoff allows for a first implementation.

**Correction:** the local commit titled "Complete durable RHDH onboarding refactor" (merged as `d1a4841`) did not complete the refactor. An unpublished draft of this log also overstated its restart coverage and state transitions, and said CI ran the drift check. This entry replaces that draft.

## Validation

Local checks at `box1-templates` `bd2feb3`: `npm run test:onboarding` (44 of 44), `npm run validate`, and `npm run check:onboarding-package` all passed. Eleven bugs were reintroduced one at a time in a scratch copy, and the tests caught each one.

### Live: `trash-service` (plugin `7594da8`, before the promotion fix)

The run reached `COMPLETE` in 417 seconds. It confirmed the phased flow and showed the remaining problem:

| Time (EST) | Event |
| --- | --- |
| 23:45:28 | Promotion PR merged |
| 23:49:07 | Argo sync started, initiated by `automated` |
| 23:49:22 | `verify` passed |

`verify` took 232 of the 417 seconds, and only 15 of those came after the sync started. `box1-workloads-dev` has no GitHub webhooks and `timeout.reconciliation` is unset, so Argo finds commits by polling.

### Live: `enterprise` (plugin `24a8dd8`, final state)

Expected: the promotion sync is requested by `box1-rhdh`, and the service deploys the recorded digest and source revision. All of the following were observed on the cluster.

| Check | Result |
| --- | --- |
| Run state | `COMPLETE`, with `PROMOTION_SYNC_REQUESTED` recorded for commit `e066449` |
| Argo sync | Initiated by `box1-rhdh`, 00:01:43 to 00:01:47 EST; the PR merged at 00:01:42 |
| Argo state | Synced and Healthy at `e066449` |
| Deployment | `sha256:ad4b61a…`, matching the record, with 1 of 1 replicas available |
| Source identity | `/api/info` returns `gitRef` `69da77b…`, matching the source revision |
| Health | `/q/health/ready` returns HTTP 200 |
| Credential Secret | Deleted |
| Lease | Released |
| Hub logs (30 minutes) | No `ONBOARDING_STATE_CONFLICT`, `HTTP 409`, or `lease lost` |

Time by step on this run:

| Step | Seconds | Share |
| --- | --- | --- |
| Image build | 90 | 45% |
| Onboarding PR open to merged | 29 | 15% |
| Promotion PR open to merged | 28 | 14% |
| Repository creation | 13 | 7% |
| `verify` | 15 | 8% |
| Everything else | 25 | 13% |
| **Total** | **200** | |

Comparing the two live runs (one run each, with the same build time of about 90 seconds):

| Measure | `trash-service` | `enterprise` |
| --- | --- | --- |
| Promotion merged to deployed | 221s | 3s |
| `verify` wait | 232s | 15s |
| Total | 417s | 200s |

### Not tested

- Live failed builds, failed syncs, restart recovery, and retries. These have unit tests only.
- Rollback. The procedure below has not been exercised.
- Whether another service merging during `platform` makes its exact-commit waits time out.
- Vendor support for this plugin approach was not assessed.

## Final operational state

| Item | State |
| --- | --- |
| Plugin on the cluster | `box1.org/onboarding-plugin-sha: 24a8dd89fd73…` |
| Management | Argo CD Application `developer-hub`, Synced and Healthy, from `platform/developer-hub` |
| `box1-gitops` `main` when verified | `2ae49af` |
| `box1-templates` `main` when verified | `9fd9821` |
| Template | `quarkus-rest-service` 1.2.0 |

There is no deliberate difference from source `main` and no temporary workaround in the cluster.

- **Duplicate onboarding syncs:** on both live runs, auto-sync and the explicit request deployed the onboarding commit about four seconds apart. Both succeeded each time. The promotion sync showed no duplicate on `enterprise`.
- **Hub permissions:** the onboarding service account can patch any Argo Application in `openshift-gitops`, not only service Applications. It cannot delete them, change workload Deployments, create Namespaces, or create RoleBindings in the service namespace checked.
- **Drift check:** `npm run check:onboarding-package` is manual for now. The CI workflow could not be pushed because the GitHub token lacks the `workflow` scope, and it is expected to need fixes.

## Recovery and follow-ups

To roll back, revert [box1-gitops#43](https://github.com/box1-org/box1-gitops/pull/43), then [box1-gitops#42](https://github.com/box1-org/box1-gitops/pull/42) if needed. Argo restores the earlier plugin and restarts Developer Hub. This is **untested**, and it does not undo merged service PRs or deployed services. Operating details are in the [runbook](../../runbooks/rhdh-onboarding-refactor.md).

Remaining work is tracked in [box1-docs#32](https://github.com/box1-org/box1-docs/issues/32), with no owner assigned:

- Complete the state model, restart tests, catalog lifecycle, and readiness failure handling.
- Publish a working drift check in CI.
- Collect timing from several comparable runs before making any performance claim.
- Finish onboarding ID propagation and task outputs.
- Remove the plugin duplication between `box1-templates` and `box1-gitops`.

Not investigated: the `FAILED` records for `tng`, `blue-wave`, and `morgan-service`, which predate this plugin.

Removing the second GitOps PR or adding a controller remains a separate architecture decision. Nothing here argues for either without measured timings and an explicit ownership, security, rollback, and provenance design.
