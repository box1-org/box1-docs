# RHDH onboarding plugin: OCI delivery

Use this runbook to release, verify, or roll back the Developer Hub onboarding plugin, and to rotate its registry credential.

**Status, 2026-11-05 (America/New_York): not yet exercised on the cluster.** Tracked in [box1-docs#34](https://github.com/box1-org/box1-docs/issues/34). The procedures below are untested until that issue records the results. Until the cutover merges, the source-copy path in [rhdh-onboarding-refactor.md](rhdh-onboarding-refactor.md) remains the live one.

## How delivery works

| Item | Value |
|---|---|
| Source | `box1-templates/plugins/box1-onboarding` |
| Image | `registry.apps.ocp.box1.org/box1-plugins/box1-onboarding-plugin` |
| Package and path | `box1-scaffolder-onboarding-dynamic`, at `box1-scaffolder-onboarding` |
| Target | RHDH 1.9.7, Backstage 1.45.3, `@red-hat-developer-hub/cli` 1.9.2 |
| Runtime reference | `platform/developer-hub/dynamic-plugins.yaml` in `box1-gitops` |
| Rollout trigger | `box1.org/onboarding-plugin-digest` in `platform/developer-hub/backstage.yaml` |
| Pull credential | Secret `rhdh/dynamic-plugins-registry-auth`, created outside Git |
| Cache | PVC `rhdh/dynamic-plugins-root` |

CI builds the image and opens a GitOps PR. It never changes the cluster. The `developer-hub` Argo CD Application is manual-sync, so each rollout needs a sync. Developer Hub is single-replica with `Recreate`, so **every rollout is a short outage**. Avoid syncing during an onboarding run.

## Release

1. Merge the plugin change to `box1-templates` `main`, with `version` in `plugins/box1-onboarding/package.json` raised. PR checks build and inspect the image.
2. Approve the release by tagging that commit:

   ```sh
   git tag onboarding-plugin-v<version> <main-commit>
   git push origin onboarding-plugin-v<version>
   ```

3. The `box1-onboarding-plugin-release` PipelineRun in `box1-ci` fails if the tag does not match the package version or the commit is not on `main`. It publishes the image, confirms the digest in the registry is this build, and opens a `box1-gitops` PR.
4. Review the PR: version, source commit, digest, plugin path, compatibility target, rollback digest, and build link. Confirm the guard check passed.
5. Merge the PR, then sync `developer-hub`.

## Verify

After the sync:

```sh
POD=$(oc -n rhdh get pod -l app.kubernetes.io/name=backstage -o name | head -1)

# The installer pulled the expected digest.
oc -n rhdh logs "$POD" -c install-dynamic-plugins | grep box1-onboarding-plugin

# The plugin loaded, with no duplicate module errors.
oc -n rhdh logs "$POD" -c backstage-backend | grep -E "box1-scaffolder-onboarding|Duplicate|box1-development-onboarding"

# The runtime, artifact, credential, and Argo ownership all agree.
git -C box1-gitops switch main && git -C box1-gitops pull
REGISTRY_TOKEN=$(oc whoami -t) python3 box1-gitops/platform/developer-hub/scripts/check-onboarding-runtime.py box1-gitops --live
```

During the transition, add `--transition` to the last command. Then onboard a test service with the `quarkus-rest-service` template and run `platform/developer-hub/scripts/verify-onboarding.cjs` inside the Hub container. A healthy pod alone does not show that onboarding works.

## Roll back

**To an earlier digest:** revert the release PR in `box1-gitops`, or use the rollback digest from its description, then sync `developer-hub`. Every release has a unique image tag, so the image pruner keeps its digest.

**To the source-copy path:** available only until the cleanup change merges. Revert the cutover PR and sync `developer-hub`. The installer should remove the `box1-scaffolder-onboarding` directory through its hash cleanup. Confirm that only one copy of the plugin is present afterwards:

```sh
oc -n rhdh exec "$POD" -c backstage-backend -- ls /opt/app-root/src/dynamic-plugins-root | grep box1-scaffolder
```

## Rotate the registry credential

The credential is a token for the read-only `box1-plugins/rhdh-plugin-puller` service account. Rotate it if it is exposed, or if the guard or installer reports `unauthorized`. The installer only reads the Secret at Pod start, and a running Hub is not affected until its next restart.

1. Delete the token Secret. Argo CD recreates it on the next `pipelines-ci` sync, and the token controller fills it in.

   ```sh
   oc -n box1-plugins delete secret rhdh-plugin-puller-token
   ```

2. Sync `pipelines-ci`, then rebuild the auth Secret. This does not print the token.

   ```sh
   TOKEN=$(oc -n box1-plugins get secret rhdh-plugin-puller-token -o jsonpath='{.data.token}' | base64 -d)
   AUTH=$(printf 'serviceaccount:%s' "$TOKEN" | base64 | tr -d '\n')
   printf '{"auths":{"registry.apps.ocp.box1.org":{"auth":"%s"}}}' "$AUTH" \
     | oc -n rhdh create secret generic dynamic-plugins-registry-auth \
         --from-file=auth.json=/dev/stdin --dry-run=client -o yaml \
     | oc apply -f -
   unset TOKEN AUTH
   ```

3. Prove the new credential works from the RHDH pod, before any restart depends on it. Use the digest in `dynamic-plugins.yaml`. The expected output is the digest and labels, with no `unauthorized` or `x509` error.

   ```sh
   oc -n rhdh get secret dynamic-plugins-registry-auth -o jsonpath='{.data.auth\.json}' | base64 -d \
     | oc -n rhdh exec -i "$POD" -c backstage-backend -- sh -c \
       'umask 077; cat > /tmp/auth.json; skopeo inspect --authfile /tmp/auth.json docker://registry.apps.ocp.box1.org/box1-plugins/box1-onboarding-plugin@<digest>; rc=$?; rm -f /tmp/auth.json; exit $rc'
   ```

Do not commit the credential. If the Secret is missing at the next restart, the installer cannot pull the image and the Hub will not start. Recreate the Secret and the Pod retries.

## Common failures

| Symptom | Likely cause | Action |
|---|---|---|
| Installer log shows `unauthorized` or `authentication required` | Secret missing or token revoked | Rotate the credential |
| Installer log shows `x509` | Reference uses the internal registry service, whose CA the installer does not trust | Use the route host |
| Backend log reports a duplicate `box1-development-onboarding` module | More than one plugin directory on the PVC | List the directory as above, and remove only the stale `box1-scaffolder-*` directory |
| Guard fails on a GitOps PR | Mutable tag, wrong path, copied source, or old mount | Fix the PR, and do not weaken the guard |
| Release fails at `approve` | Tag and package version differ, or the commit is not on `main` | Delete the tag and tag the right commit |

Do not clear the whole PVC to fix a plugin. It also holds `dynamic-plugins.extensions.yaml`, the UI-managed plugin choices.
