# RHDH onboarding plugin: delivery as an immutable OCI artifact

**Date:** 2026-11-05 (America/New_York)
**Status:** Complete. Tracked in [box1-docs#34](https://github.com/box1-org/box1-docs/issues/34). Background is in the [phased onboarding log](2026-11-04-rhdh-onboarding-refactor.md).

## Outcome

Developer Hub now installs the onboarding plugin from a versioned OCI image pinned by digest. `box1-gitops` holds only the reference, so a plugin change no longer means copying source between repositories and opening two matching PRs.

```text
oci://registry.apps.ocp.box1.org/box1-plugins/box1-onboarding-plugin@sha256:bf3368149ef66e00dbc1699ecb4d0b871f5b7d99995a4054c4eaec9b44e61a94!box1-scaffolder-onboarding
```

The artifact passed an install, a warm restart, an upgrade to a second digest, a rollback to the first, and a real onboarding run. The old path has been removed. CI publishes images and proposes GitOps PRs, and Argo CD remains the only deployer.

## Starting baseline

The plugin reached the Hub through a source copy:

1. `npm run package:onboarding` copied `box1-templates/plugins/box1-onboarding` to `box1-gitops/platform/developer-hub/onboarding/plugin`.
2. A `configMapGenerator` turned the copy into the `developer-hub-onboarding-plugin` ConfigMap.
3. The Pod mounted it at `/onboarding-plugin-source`, and `install-extensions.py` staged the files into an emptyDir.
4. The RHDH installer packed the local package onto the `dynamic-plugins-root` PVC, as `box1-scaffolder-onboarding-dynamic-1.1.0`.

The wrapper deleted this plugin's cache hash on every boot to work around the 1.9 installer's stale-hash cleanup. A checksum annotation triggered rollouts. The drift check was manual, and its CI workflow had never run.

The environment was RHDH Operator 1.9.7 and Backstage 1.45.3, with one replica and the `Recreate` strategy. `box1-templates` was not registered with Pipelines as Code.

## What changed

| Phase | PR | Merge | Change |
|---|---|---|---|
| 2, 3 | [box1-gitops#45](https://github.com/box1-org/box1-gitops/pull/45) | `c635fdf` | `box1-plugins` image project, CI and pull identities, `box1-templates` PaC Repository |
| 1, 3 | [box1-templates#16](https://github.com/box1-org/box1-templates/pull/16) | `5c47ce3` | Pinned CLI, packaging and inspection commands, PR and release pipelines, GitOps PR generator |
| 3 | [box1-templates#17](https://github.com/box1-org/box1-templates/pull/17) | `45c02c2` | Checksum-verified `kubectl` for validation in CI |
| 3 | [box1-templates#18](https://github.com/box1-org/box1-templates/pull/18) | `c3cb838` | Version 1.1.1, the first published artifact |
| 4, 7 | [box1-gitops#46](https://github.com/box1-org/box1-gitops/pull/46) | `556e123` | Runtime cutover and drift guard |
| 5 | [box1-templates#19](https://github.com/box1-org/box1-templates/pull/19) | `63be64f` | Version 1.1.2, for the second digest |
| 5 | [box1-gitops#47](https://github.com/box1-org/box1-gitops/pull/47) | `a1b5753` | Upgrade, opened by the release pipeline |
| 5 | [box1-gitops#48](https://github.com/box1-org/box1-gitops/pull/48) | `5947583` | Rollback |
| 6 | [box1-gitops#50](https://github.com/box1-org/box1-gitops/pull/50) | `cba8b2e` | Removed the copy, generator, staging code, and guard transition mode |
| 6 | [box1-templates#20](https://github.com/box1-org/box1-templates/pull/20) | `541990f` | Removed the copy scripts and old documentation |
| Docs | [box1-docs#35](https://github.com/box1-org/box1-docs/pull/35) | `0533e8e` | [Runbook](../../runbooks/rhdh-onboarding-plugin-oci.md) |

The source is unchanged apart from its version number, so the running code matches what the copy delivered.

**Decisions with consequences:**

- **The package name is preserved through staging.** The RHDH CLI always derives `${name}-dynamic`, which would have produced `…-dynamic-dynamic`. Packaging stages a copy named `box1-scaffolder-onboarding`, so the runtime package stays `box1-scaffolder-onboarding-dynamic` and the image path is `box1-scaffolder-onboarding`.
- **The CLI is pinned to 1.9.2.** That is npm's `release-1.9` tag, with a lockfile in `tools/rhdh-cli`. A test ties its minor version to the RHDH compatibility target. This compatibility rests on the tag and on the results below, and vendor support for the combination is not established.
- **The image has its own project in the existing registry.** Registry roles are per-project, so a pull credential on `box1-ci` could have read every service image.
- **The registry route is the endpoint.** From the RHDH pod its public certificate verifies, while the internal service fails with `x509: unknown authority`.
- **The init-container command override stays.** `install-extensions.py` also merges UI-managed Extensions plugins. Only its staging block was removed, so this differs from removing the custom init-container outright.
- **Two CI identities can use `pipelines-scc`, running as root.** A cluster probe showed buildah cannot run under the restricted SCC. PR builds use `ci-plugin-check`, which has no registry permissions.
- **CI runs on Tekton.** A GitHub Actions workflow could not be pushed with the available token, and Tekton matches the rest of Box1. A release is approved by tagging a `main` commit `onboarding-plugin-v<version>`.
- **No signing was added.** Digest pinning was the requirement, and signing was not a prerequisite.

## Validation and evidence

Full results are in the [#34 comments](https://github.com/box1-org/box1-docs/issues/34). Each test ran once, so the times below are observations and establish no performance result.

| Test | Expected | Observed |
|---|---|---|
| First install on the existing PVC, `556e123` | Pull by digest, old directory removed | Installed `bf33681…` with the pull Secret. The installer removed `-1.1.0`. Ready in about 70 seconds |
| Warm restart | No new pull | `Skipping download of already installed dynamic plugin`. Ready in 57 seconds |
| Upgrade to 1.1.2, `a1b5753` | New digest replaces the old | Installed `bdfaa23…`, with one directory on disk. Ready in 67 seconds |
| Rollback, `5947583` | Earlier digest restored | Installed `bf33681…`, version 1.1.1. Ready in 68 seconds |
| Cleanup, `cba8b2e` | Only the source ConfigMap pruned, wrapper boots | Pruned as expected. A restart with the changed wrapper was ready in 55 seconds, with no errors |
| Pull credential | Reads plugins only | Reads `box1-plugins`. Reading `box1-ci` returns `authentication required`. `oc auth can-i` denies pushing |
| Guard | Rejects violations | Self-test rejects 23 violations. A real pipeline failed on a mutable tag ([#49](https://github.com/box1-org/box1-gitops/pull/49), closed unmerged) |

After each rollout, the backend log showed the plugin loaded from `box1-scaffolder-onboarding` with no duplicate errors. `dynamic-plugins.extensions.yaml` kept the same checksum throughout (`9b11c59d…`), so UI-managed choices were preserved. After the first install and the cleanup, the scaffolder API listed all 10 `box1:` actions.

**End-to-end onboarding.** The user ran `post-show` through the Hub on digest `bf33681…`, and the results were checked on the cluster:

- The status record reached `COMPLETE` through all 16 states, from 06:06:08 to 06:09:26 UTC.
- Repository `box1-org/post-show` was created at source `eb2130f`, and [box1-workloads-dev#45](https://github.com/box1-org/box1-workloads-dev/pull/45) and [#46](https://github.com/box1-org/box1-workloads-dev/pull/46) merged.
- `onb-post-show-eb2130fe` succeeded, its credential Secret was deleted, and the Lease was released.
- The Deployment ran the recorded image digest. `/q/health/ready` returned HTTP 200, and `/api/info` reported the source revision.
- Argo was Synced and Healthy, and `component:default/post-show` resolved with `post-show-api`.

The UI steps were performed by the user and were not independently observed.

**Failures along the way:**

- The first release, tagged `onboarding-plugin-v1.1.0`, failed because the build image had no `kubectl`. Nothing was published. Force-moving the tag was denied by the session's permission check, so the release moved to 1.1.1 and the 1.1.0 tag remains on `5c47ce3`.
- A generator test caught a regular expression that consumed a newline, before any release used it.

**Not tested:**

- An install on an empty PVC. The PVC holds UI-managed choices, so the first install used the existing one.
- Registry credential rotation. The runbook procedure has not been run.
- Rollback from OCI to the source-copy path, by the user's decision.
- Onboarding after the cleanup. `post-show` ran before it, and the cleanup removed only inactive code.
- A signed-in UI session after the cutover, beyond the `post-show` run.

## Final operational state

| Item | State |
|---|---|
| Runtime plugin | Version 1.1.1 from `c3cb838`, digest `sha256:bf33681…` |
| Desired state | `box1-gitops` `platform/developer-hub`, at `cba8b2e` when verified |
| Management | Argo CD `developer-hub` (manual sync) owns the `Backstage` CR, and the Operator owns the Deployment |
| CI | `.tekton/onboarding-plugin-pr.yaml` and `onboarding-plugin-release.yaml` in `box1-templates`, and `.tekton/onboarding-plugin-guard.yaml` in `box1-gitops` |
| Pull credential | Secret `rhdh/dynamic-plugins-registry-auth`, created by hand outside Git from the `box1-plugins/rhdh-plugin-puller` service account token. It is not Argo-managed |
| Cache | PVC `dynamic-plugins-root`, unchanged |

**Deliberate differences:**

- `box1-templates` `main` is at version 1.1.2 and the runtime is on 1.1.1, because rollback was the last test. Only the version number differs. The next release must be 1.1.3 or higher.
- Versions 1.1.0 and 1.1.2 have tags. No image exists for 1.1.0.

## Recovery and follow-ups

**Recovery:** revert the release PR, or restore the rollback digest from its description, then sync `developer-hub`. This was exercised through #48. The [runbook](../../runbooks/rhdh-onboarding-plugin-oci.md) covers release, verification, rollback, and credential rotation.

**If the pull Secret is missing at a restart:** an uncached digest cannot be pulled, and the Hub will not start. Recreate the Secret using the runbook.

**Returning to the source-copy path:** this needs reverting both #46 and #50, and has not been tested.

**Known limitations, with no backlog issue filed:**

- The untested items above, particularly credential rotation.
- The Extensions adapter still replaces the installer's command, and depends on the installer's text. Revalidate it with each Operator upgrade.
- The guard's `--live` check is run by hand after a sync. CI runs only the static and registry checks, because the Application is manual-sync.

**Related:** remaining failure-path and timing work stays in [box1-docs#32](https://github.com/box1-org/box1-docs/issues/32). Task 13 there is complete.
