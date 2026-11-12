# Forgejo proof transaction: evidence and go/no-go

Backlog: [box1-docs#164](https://github.com/box1-org/box1-docs/issues/164). Run on the Box1 lab on 2026-11-11 (America/New_York); the timestamps below are UTC, 2026-11-12.

## Verdict

**Go, with known gaps.** Forgejo can host the Box1 delivery lane. The full transaction succeeded once, end to end, on the Box1 cluster:

> RHDH creates a private repository → Dev Spaces opens it and pushes a change → Pipelines as Code validates it → automation opens and safely merges a GitOps promotion → Argo CD deploys the expected image.

All five kill-criteria passed. None of the gaps blocks the lane. Each one is listed under [Gaps and follow-ups](#gaps-and-follow-ups), with its workaround and cost.

Scope:
- The proof ran on the self-hosted Box1 cluster, not on RHPDS. Replaying it on an RHPDS environment is **not tested**.
- It uses Box1's existing RHDH, Dev Spaces, Pipelines and Argo CD.
- The GitHub golden path was not changed.

## Starting baseline

Every part of the golden path was tied to GitHub:
- the RHDH GitHub App and the `box1-onboarding` plugin
- the Pipelines as Code GitHub App and its Repository CRs
- the Dev Spaces GitHub OAuth secret
- `box1-gitops/platform/pipelines/tasks/gitops-promote.yaml`, which uses GitHub check-runs and a squash merge pinned to a SHA

No Forgejo or Gitea work existed.

Cluster versions:

| Component | Version |
|---|---|
| OpenShift | 5.0.0-rc.7 (single node) |
| Red Hat Developer Hub | 1.9.7 |
| Dev Spaces | 3.29.1 |
| OpenShift Pipelines | 1.24.3 |
| OpenShift GitOps | 1.22.2 |

## What was built

| Piece | Where | Notes |
|---|---|---|
| Forgejo 17.0.1 | `box1-gitops` `platform/forgejo/` (namespace `forgejo`), Argo CD app `forgejo` | Rootless image pinned by digest. SQLite on a 10 Gi PVC. Edge Route `forgejo.apps.ocp.box1.org`. SSH, registration, Actions and packages are off. Server secrets are generated onto the PVC, so none are in Git. |
| Bootstrap | `platform/forgejo/bootstrap/bootstrap.py` (Sync and PostSync hook Jobs) | Idempotent. Creates the org `box1-fj` with teams `writers`, `readers` and `ci-admins`, and the bot accounts `rhdh-bot`, `pac-bot`, `promote-bot`, `argocd-bot` and `box1-dev`, each with a scoped token. Creates the private repo `workloads-proof` with branch protection, an org webhook to the PaC controller, and the consumer Secrets. A re-run keeps tokens that still work. |
| RHDH | `platform/developer-hub/` (additive) | `integrations.gitea` for the Forgejo host, using the `rhdh-bot` token from `developer-hub-forgejo-secrets`. Gitea scaffolder module from the RHDH overlay registry, `backstage-plugin-scaffolder-backend-module-gitea@sha256:3e798b0a…` (0.2.15); it is not bundled in RHDH 1.9. |
| Template | `box1-templates` `templates/forgejo-proof-service/` | `fetch:template` → `publish:gitea` (private) → `catalog:register`. Skeleton: Python HTTP service, Containerfile, devfile, and `.tekton` PR and push runs. |
| PaC lane | `platform/forgejo/ci/` (namespace `box1-fj-ci`) | Repository CRs with `git_provider.type: gitea` and `pipelinerun_provenance: default_branch`. A registrar CronJob creates the CRs for new org repos. |
| `forgejo-gitops-validate` | `ci/tasks.yaml`, `ci/validate.py` | Required PR check on `workloads-proof`. Only `apps/<name>/{deployment,service,route}.yaml` may change. Only those kinds are allowed, only in namespace `box1-fj-dev`, and images must be the CI registry path pinned by digest. |
| `forgejo-gitops-promote` | `ci/tasks.yaml`, `ci/promote.py` | Port of the guards in `gitops-promote.yaml`. See [Safe-merge guards](#safe-merge-guards). |
| Argo CD | `ci/argocd.yaml` | Application `forgejo-proof-workloads`: private Forgejo repo, path `apps`, plain manifests, no automated sync. The promote Task syncs exactly the merge commit. Repository credential: `openshift-gitops/forgejo-repo-creds` (`argocd-bot`, read-only). |

### Safe-merge guards

`forgejo-gitops-promote` runs these checks in order:
1. The source revision is still the head of the service's `main`.
2. It creates one commit on a `promote/` branch that touches only the expected files.
3. It re-checks the PR author, head SHA and file list.
4. It waits for the required status contexts to pass on the exact head.
5. Just before merging, it re-checks the head, the PR state and the source `main`.
6. It squash-merges with `head_commit_id` pinned.
7. Argo CD syncs to the merge commit and must reach Synced/Healthy.
8. A Ready pod must run the promoted digest.
9. The service's HTTP response must report the source revision.

Branch protection on `workloads-proof` `main` has four rules:
- Only `box1-admin` may push directly, for break-glass and seeding.
- Only `promote-bot` and `box1-admin` may merge.
- The required context is `Pipelines as Code CI / workloads-proof-validate*`.
- A PR whose branch is behind `main` cannot be merged (`block_on_outdated_branch`).

## The transaction (clean run)

| Step | Evidence |
|---|---|
| RHDH creates a private repo | Scaffolder task `a4f41468-7e2d-483b-bbde-ef5d57552d45` ran from the RHDH UI after an OIDC sign-in. It created `box1-fj/fj-proof` with `private: true` and registered `component:default/fj-proof`. Anonymous API access returned 404, and `git ls-remote` without credentials was refused. |
| Dev Spaces opens it and pushes | Workspace `fj-proof-envq` was started from `https://devspaces…/#https://forgejo…/box1-fj/fj-proof`. It cloned the private repo through a per-user `git-credentials` Secret. It ran on the repo's devfile: component `tools`, commands `test` and `run`. From the workspace: the greeting was edited, unit tests passed, and the commit `d2528b9e` was pushed to a branch. PR `fj-proof#2` was opened as `box1-dev`. |
| PaC validates | Run `fj-proof-pull-request-qqmpz` did clone → unittest → buildah build. Forgejo status `Pipelines as Code CI / fj-proof-pull-request`: success. The PR was merged with `head_commit_id` pinned, giving merge commit `ed77f412`. |
| Build and promote | Push run `fj-proof-push-9q6gk` built `box1-fj-ci/fj-proof@sha256:d2ae51e9c87502a7d6f80cbd9bf9cd11522ee84a3b2eb16dd56b557fc6821c54`. `promote-bot` opened `workloads-proof#3` with head `ee570efa`. `workloads-proof-validate` passed on that exact head. The PR was squash-merged pinned to the head; merge commit `62fb7bbbf841c6503d421c564e849c3a763cdbec`. |
| Argo CD deploys | `forgejo-proof-workloads`: Synced/Healthy at `62fb7bbb`, and the operation succeeded at that revision. Pod `fj-proof-7f6f94dd6c-6szp2` is Ready and its `imageID` ends in `sha256:d2ae51e9…`. `https://fj-proof-box1-fj-dev.apps.ocp.box1.org/` returned `{"service": "fj-proof", "message": "Hello from fj-proof: Dev Spaces to Argo CD via Forgejo", "revision": "ed77f41224279df55e2e03abee55cc9d33f3d157"}`. |

Promote Task results: `promoted=true`, `merge-commit=62fb7bbb…`, `pr-url=…/workloads-proof/pulls/3`.

## Kill-criteria

| # | Criterion | Result |
|---|---|---|
| 1 | RHDH: the Gitea scaffolder loads, and `publish:gitea` creates a **private** repo | **Pass.** The module is not bundled in RHDH 1.9 and was loaded as an OCI dynamic plugin. Its `repoContentsUrl` output omits the branch, so the template registers an explicit `…/src/branch/main/catalog-info.yaml` instead. |
| 2 | Dev Spaces: opens the Forgejo repo with its devfile and pushes | **Pass, with a workaround.** The factory URL fails first: che-server sends unknown hosts to its GitHub parser (`No PersonalAccessTokenFetcher configured`) and tries `raw.forgejo…`. **Continue with default devfile** then clones the repo using the `git-credentials` Secret and applies the repo devfile. Push works. |
| 3 | PaC: `gitea` provider on Forgejo; PR and push triggers, status write-back, `/retest` | **Pass.** `pac-bot` must be in a repo-admin team, because PaC looks up the PR author's repo permission. |
| 4 | Safe merge: branch protection, required contexts, pinned head; stale head rejected | **Pass.** See [Negative checks](#negative-checks). |
| 5 | Argo CD from a private Forgejo repo over TLS | **Pass.** It uses a `repo-creds` Secret and the ingress wildcard certificate (Let's Encrypt). |

## Negative checks

| Check | Result |
|---|---|
| Anonymous read of a private repo | Denied: API 404, `git ls-remote` refused |
| Direct push to `workloads-proof` `main` as `box1-dev` (a writer) | `remote: Forgejo: Not allowed to push to protected branch main`, pre-receive hook declined |
| Merge of `workloads-proof#2` by `box1-dev` (not on the merge allowlist) | `User not allowed to merge PR` |
| Merge of `workloads-proof#2` by `promote-bot` with `head_commit_id` set to a stale SHA | HTTP 409 `head out of date` |
| Disallowed file in a promotion PR (`apps/probe/configmap.yaml`, `workloads-proof#1`) | `workloads-proof-validate` failed: only deployment, service and route files may change |
| Failed required check during promotion (first run, `fj-proof-push-rvbzk`) | promote-bot opened `workloads-proof#2`, saw the failed check and stopped without merging. The cause was a validate Task bug, since fixed: rendering put the pod's namespace into the manifests. |

## Problems found and fixed during the run

All the fixes are on the `forgejo-proof` branches:
- **Sync deadlock:** the PVC must share the Deployment's sync wave, because `lvms` binds only when a pod uses the claim.
- **Argo CD access:** the namespaces need `argocd.argoproj.io/managed-by: openshift-gitops`.
- **RUN_USER:** Forgejo refuses to start unless `RUN_USER` equals the arbitrary UID OpenShift assigns. The init container writes the actual UID into the config.
- **Token check:** a narrowly scoped token gets 403 from `/user`, and that still counts as a valid token.
- **PaC admission:** the webhook admits a Repository CR only from a user who may create PipelineRuns. The registrar's Role now allows that.
- **Validate Task:** the steps need a fixed non-root UID; the diff base is the merge base with the target branch; and rendering uses `oc create --dry-run=client -n box1-fj-dev`.
- **Template:** the catalog URL is now explicit, because `publish:gitea` returns `repoContentsUrl` without the branch.

## Final operational state

- **Argo CD apps `forgejo` and `developer-hub`** are synced from `box1-gitops` branch `forgejo-proof` and Healthy.
  - This intentionally differs from `main` until the branch PR merges.
  - `developer-hub` is `main` (`50c96aa`) plus the three additive Forgejo edits. These are in commit `42955af`, despite that commit's RUN_USER message.
- **Template `forgejo-proof-service`** is registered in the catalog from `box1-templates` branch `forgejo-proof`.
- **Hand-made state:** the Secret `mike-devspaces/forgejo-git-credentials`, holding the `box1-dev` token. Creating it is a per-user step.
- **Running proof workloads:** `box1-fj-dev/fj-proof` (Argo-managed) and the Dev Spaces workspace `fj-proof-envq`.
- **Extra repository:** `box1-fj/fj-hello` is left over from the first template run, which failed at catalog registration. It has no pipelines run and nothing deployed.
- **Regression:** all 56 Argo CD applications are Healthy, and the GitHub templates are still listed in RHDH.

## Recovery

| What to undo | How |
|---|---|
| Whole proof | Delete the Argo CD apps `forgejo-proof-workloads` and `forgejo`; deleting `forgejo` with prune removes the namespaces `forgejo`, `box1-fj-ci` and `box1-fj-dev`. Then delete `openshift-gitops/forgejo-repo-creds`, `rhdh/developer-hub-forgejo-secrets` and `mike-devspaces/forgejo-git-credentials`. |
| RHDH change | Sync `developer-hub` back to `main`. The `developer-hub-forgejo-secrets` reference is the only one that needs the Secret to exist. |
| Template | Unregister the catalog location for `forgejo-proof-service`. |
| Forgejo data | Lives only on the `forgejo-data` PVC. There is no backup (**not tested**). |

## Gaps and follow-ups

| Gap | Workaround now | Cost to close |
|---|---|---|
| The `box1-onboarding` plugin is GitHub-only | Stock `publish:gitea` template | Add a Forgejo provider to `workflow.cjs`, with repository, PR and merge calls |
| No PaC auto-configure for Forgejo | Registrar CronJob (2 min) | Small. Could move into onboarding |
| Dev Spaces factory doesn't resolve Forgejo URLs | **Continue with default devfile**, plus a per-user token Secret | Upstream Che support for Gitea/Forgejo, or a dashboard-free DevWorkspace creation path |
| `pac-bot` needs repo-admin | Dedicated `ci-admins` team; token without `admin:*` scope | Accept, or an upstream PaC change |
| Gitea scaffolder module is not bundled in RHDH 1.9 | OCI plugin pinned by digest | Track RHDH support status; vendor support is not established |
| Host names in `ci/*.yaml` and the template are not parameterized | Edit by hand per cluster | Kustomize replacements, or template values |
| RHPDS replay | **Not tested** | Run the bootstrap on a fresh RHPDS environment |
| Forgejo backup and restore | None | PVC snapshot or `forgejo dump` CronJob |
