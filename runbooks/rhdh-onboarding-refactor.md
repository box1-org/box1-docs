# RHDH onboarding durable workflow

The Box1 onboarding plugin splits development onboarding into phases that can be retried separately. For how this was delivered and tested, see the [achievement log](../achievements/2026/2026-11-04-rhdh-onboarding-refactor.md). Remaining work is tracked in [box1-docs#32](https://github.com/box1-org/box1-docs/issues/32).

## Phases

The Quarkus template (1.2.0) runs these actions in order. `box1:development:onboard` is a compatibility wrapper that runs the same five `box1:development:` phases.

| Action | What it does | Ends when |
| --- | --- | --- |
| `box1:repository:ensure` | Creates or resumes the owned source repository | The source commit is recorded |
| `box1:catalog:submit` | Submits the catalog location | The location is submitted; it does not wait for processing |
| `box1:development:provision` | Validates and merges the onboarding PR | The PR is merged |
| `box1:development:platform` | Syncs the workload index and requests the service sync | The build prerequisites exist: active Namespace, `ci-build` ServiceAccount, registry push binding |
| `box1:development:build` | Runs the first build while the remaining platform checks finish | The digest is recorded and platform readiness has passed |
| `box1:development:promote` | Merges the promotion PR and requests an Argo sync to its merge commit | The sync is requested or found unnecessary |
| `box1:development:verify` | Checks Argo, the Deployment image, the Route, `/q/health/ready`, and `/api/info` | All checks pass |
| `box1:catalog:verify` | Waits for the catalog entity | The expected entity exists |

Scaffolder steps run one at a time, so the build and readiness overlap happens inside `box1:development:build`. This keeps the credential Secret's lifecycle inside one action.

Inside that step, a build failure stops the platform observers. A platform failure lets the build finish, so its digest is kept and a retry does not rebuild.

## Inspect a run

```bash
# Durable state: phase, status, PRs, digest, promotion sync, and history
oc -n rhdh get configmap box1-onboard-SERVICE -o jsonpath='{.data.status\.json}'

# Concurrency Lease: the holder is empty once a task finishes
oc -n rhdh get lease box1-onboard-SERVICE -o jsonpath='{.spec.holderIdentity}'

# Who initiated each sync: automated, or username box1-rhdh
oc -n openshift-gitops get application SERVICE -o jsonpath='{.status.history}'
```

The status record stores external identifiers and Secret names, never credential values. `activeWaits` lists the waits that were in progress at the last write.

## Retry behaviour

Retry a failed task by resubmitting the template with the same parameters. Recorded repositories, PRs, PipelineRuns, digests, and sync requests are reused rather than repeated.

- **Failed Argo sync:** a failed operation blocks a new sync request, and a retry does not start one. If the operation stays failed, fix the cause and sync the Application manually, then retry.
- **Failed build:** a retry starts a new PipelineRun, up to three recorded attempts.
- **Lease conflict:** a second task for the same service is refused until the Lease is released or expires.
- **State conflict:** `ONBOARDING_STATE_CONFLICT` means another process changed the status record. Check for a second task before retrying.

Retry and restart behaviour is covered by unit tests only. It has **not been tested** on the live cluster.

## Packaging

`box1-org/box1-templates` holds the canonical plugin in `plugins/box1-onboarding`. `box1-gitops/platform/developer-hub/onboarding/plugin` holds a generated copy. Do not edit the copy by hand.

1. Change the canonical source in `box1-templates`.
2. With both repositories checked out side by side, run `npm run package:onboarding` from `box1-templates`.
3. Run `npm run check:onboarding-package` to confirm the copy and checksum match.
4. Open PRs in both repositories.

Merging the `box1-gitops` change updates `box1.org/onboarding-plugin-sha`, which restarts Developer Hub. Avoid merging during an onboarding run.

The drift check is currently **manual**. The CI workflow for it is not yet published.

## Rollback

Revert the most recent `box1-gitops` packaging PR. Argo restores the previous plugin and checksum, and Developer Hub restarts. This procedure has **not been tested**.

Reverting does not undo merged service PRs or deployed services.

## Known limitations

- The state model does not yet write `pending` or `running`, and it has no `phaseAttempt` field.
- Readiness failures keep polling until the 15-minute timeout, and the timeout error does not name the blocking conditions.
- Catalog status is only `submitted` or `ready`.
- `platform` sync waits require the exact merge commit, so another service merging during onboarding could make them time out. This has not been tested.
- If auto-sync gets there first, an explicit request can produce a second sync of the same revision. Both have succeeded so far.
- The onboarding service account can patch any Argo Application in `openshift-gitops`, not only service Applications. It cannot delete them.
