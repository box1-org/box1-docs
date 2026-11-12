# GitLab CE proof transaction: evidence and comparison with Forgejo

This is a re-run of the [Forgejo proof transaction](forgejo-proof-transaction.md) ([box1-docs#164](https://github.com/box1-org/box1-docs/issues/164)) on GitLab CE. It ran on the Box1 lab on 2026-11-11 (America/New_York); the timestamps below are UTC, 2026-11-12.

The transaction and the safety checks are the same as for Forgejo. The Forgejo lane kept running alongside, unchanged.

## Verdict

**Pass.** The full transaction ran once from end to end on GitLab CE 19.5.4:

> RHDH creates a private project → Dev Spaces opens it and pushes a change → Pipelines as Code validates it → automation opens and safely merges a GitOps promotion → Argo CD deploys the expected image.

All five kill-criteria passed. GitLab needed fewer workarounds than Forgejo. In exchange, it runs a root-capable container (the `anyuid` SCC) and uses about 2.8 GiB of memory, against Forgejo's much smaller footprint. Forgejo's memory was not measured in this run.

Scope:
- The run used the Box1 cluster, not RHPDS; the RHPDS replay is **not tested**.
- GitLab was upgraded from 19.5.1 to 19.5.4 during the run, after the PR check and before the merge. The rest of the transaction ran on 19.5.4.

## What was built

| Piece | Where | Notes |
|---|---|---|
| GitLab CE 19.5.4 (Omnibus) | `box1-gitops` `platform/gitlab/` (namespace `gitlab`), Argo CD app `gitlab` | One pod with a 20 Gi PVC (`etc` and `opt` subPaths). Edge Route `gitlab.apps.ocp.box1.org`. Pinned `gitlab/gitlab-ce@sha256:fde2dacd…`. |
| Memory settings | `platform/gitlab/gitlab.rb` | Limit 4 GiB, request 3 GiB. Settings: Puma single mode (`worker_processes 0`), Sidekiq concurrency 5, PostgreSQL `shared_buffers` 128 MB, jemalloc decay. Off: Prometheus and exporters, registry, KAS, Pages, Mattermost, packages, dependency proxy, email. |
| Root token | `seed-token.sh`, run inside the GitLab container | Makes sure root has a personal access token equal to the generated `gitlab-admin` Secret. It runs one `gitlab-rails runner` call, and only when the token doesn't work yet. Nothing secret is in Git. |
| Bootstrap | `platform/gitlab/bootstrap/bootstrap.py` | Idempotent. See [Bootstrap](#bootstrap). |
| RHDH | `platform/developer-hub/` (additive) | `integrations.gitlab` using the `rhdh-bot` token from `developer-hub-gitlab-secrets`. Enables the bundled GitLab scaffolder module (`publish:gitlab`). |
| Template | `box1-templates` `templates/gitlab-proof-service/` | `publish:gitlab` (private), then `catalog:register` using `repoContentsUrl` (the stock output works). The skeleton is the same as the Forgejo template. |
| PaC lane | `platform/gitlab/ci/` (namespace `box1-gl-ci`) | Repository CRs with `git_provider.type: gitlab`. The registrar CronJob creates the Repository CR **and** the project webhook (CE has no group webhooks). The validate Task is the Forgejo one. `gitlab-gitops-promote` ports the same guards to the GitLab API: one commit plus an MR, author/head/file-list checks, required status on the exact head, then `PUT …/merge?sha=<head>&squash=true`. |
| Argo CD | `ci/argocd.yaml` | Application `gitlab-proof-workloads`. Repository credential `openshift-gitops/gitlab-repo-creds` (`argocd-bot`, `read_repository`). |

### Bootstrap

It configures:
- **Instance settings:** sign-up off, private by default, public visibility restricted, outbound requests allowed only to the PaC controller Service.
- **Groups:** `box1-gl` for services and `box1-gl-gitops` for the GitOps repo.
- **Bot accounts:** each has a scoped token.
- **`workloads-proof`:**
  - "Pipelines must succeed" is on.
  - `main` is protected: nobody may push, Maintainers merge.
  - It has a project webhook to the PaC controller.
- **Consumer Secrets:** the same set as for Forgejo.

### Access model

GitLab CE protects branches by role, not by user. So "only the promotion bot may merge" is enforced by group membership:

| Account | `box1-gl` (services) | `box1-gl-gitops` | Token scopes |
|---|---|---|---|
| `rhdh-bot` | Developer (creates projects; initial push allowed) | none | `api` |
| `pac-bot` | Maintainer (creates project webhooks) | Developer | `api` |
| `promote-bot` | Reporter | **Maintainer: the only one** | `api` |
| `argocd-bot` | Reporter | Reporter | `read_repository` |
| `box1-dev` | Maintainer (service owner) | Developer | `api`, `write_repository` |

## The transaction

| Step | Evidence |
|---|---|
| RHDH creates a private project | Scaffolder task `3f45599f…` ran from the RHDH UI after an OIDC sign-in. It created `box1-gl/gl-svc` with `visibility: private` and registered `component:default/gl-svc` using `repoContentsUrl` directly. Anonymous API access returned 404. |
| Dev Spaces opens it and pushes | The factory URL `https://devspaces…/#https://gitlab.apps.ocp.box1.org/box1-gl/gl-svc` resolved `devfile.yaml` **directly from the private project**: the devfile-source annotation shows `scm: repo …/gl-svc.git, fileName: devfile.yaml`. It used a standard Dev Spaces GitLab personal access token Secret. Workspace `gl-svc` ran the repo devfile (`tools`, `test`, `run`). The greeting was edited, unit tests passed, and commit `b5767307` was pushed. MR `gl-svc!1` was opened as `box1-dev`. |
| PaC validates | `gl-svc-pull-request-bhtpt` passed. Status `Pipelines as Code CI / gl-svc-pull-request` was success, and `detailed_merge_status` was `mergeable`. Merged pinned with `sha=`; merge commit `127d3bc7`. |
| Build and promote | Push run `gl-svc-push-jn8jm` (recovered with `/retest`, see below) built `box1-gl-ci/gl-svc@sha256:f28f875ff3a7755f95c382e247626d869d04f25a3c66f9bc1506b62fdd014b70`. `promote-bot` opened `workloads-proof!3` with head `cc233351`. `workloads-proof-validate` passed on that head. It squash-merged pinned to the head; merge commit `b64a8565b2b9e3e55792375f7d330f93537cc82f`. |
| Argo CD deploys | `gitlab-proof-workloads`: Synced/Healthy at `b64a8565`. Pod `gl-svc-6cf889df47-d7zqm` is Ready with an `imageID` ending in `sha256:f28f875f…`. `https://gl-svc-box1-gl-dev.apps.ocp.box1.org/` returned `{"service": "gl-svc", "message": "Hello from gl-svc: Dev Spaces to Argo CD via GitLab", "revision": "127d3bc7913321d79a26436682a7cf089175b519"}`. |

## Negative checks

| Check | Result |
|---|---|
| Anonymous read of private projects | API 404; `git ls-remote` refused |
| Direct push to `workloads-proof` `main` as `box1-dev` | `GitLab: You are not allowed to push code to protected branches on this project.` |
| Merge by `box1-dev` (Developer in the GitOps group) | HTTP 401 (on both 19.5.1 and 19.5.4) |
| Merge by `promote-bot` while the required check failed (probe MR `!1`, on 19.5.1) | HTTP 405. `detailed_merge_status: ci_must_pass`, `head_pipeline.source: external`. **CE's "Pipelines must succeed" honors PaC's external commit statuses.** |
| Merge by `promote-bot` pinned to a stale SHA (`!2`) | HTTP 409 `SHA does not match HEAD of source branch` |
| Disallowed file in a promotion MR (`apps/probe/configmap.yaml`, `!1`) | `workloads-proof-validate` failed |
| Promotion guard failure (first push run `gl-svc-push-g265l`) | The file-list check failed and nothing was merged. The cause was a race in the promote Task: GitLab computes MR diffs asynchronously. It is now fixed: the Task waits for `diff_refs.head_sha`. |
| Recovery | A `/retest` comment on the pushed merge commit started a new push run (`gl-svc-push-jn8jm`), which succeeded. On GitHub this path failed ([#64](https://github.com/box1-org/box1-docs/issues/64)); Forgejo has no equivalent. |

## Problems found and fixed during the run

- **Project creation lock:** `project_creation_level: noone` also blocks admins. The bootstrap now creates the GitOps project first and locks the group afterwards.
- **First push blocked:** GitLab's default branch protection blocked `rhdh-bot`'s (Developer) first push to a new project. The service group's `default_branch_protection_defaults` now sets `developer_can_initial_push: true`. A first attempt left the empty project `box1-gl/gl-proof`.
- **Template input:** `publish:gitlab` takes `description` under `settings`, not as a top-level input.
- **Diff race:** see the promotion guard failure in [Negative checks](#negative-checks).

## Forgejo and GitLab side by side

| Concern | Forgejo 17.0.1 | GitLab CE 19.5.4 |
|---|---|---|
| Footprint | One rootless pod with SQLite (memory not measured) | One Omnibus pod. 2.6–2.9 GiB in steady state, under a 4 GiB limit. About 4.5 min to Ready on first boot. |
| Pod security | `restricted-v2`. Needs `RUN_USER` set to the assigned UID. | Needs the **`anyuid`** SCC; Omnibus starts as root. |
| RHDH scaffolder | Not bundled; community OCI plugin. `repoContentsUrl` bug, worked around. | **Bundled** module. Stock output works. |
| Dev Spaces | Factory fails. Workaround: **Continue with default devfile** plus a generic `git-credentials` Secret. | **Factory resolves the devfile natively**, using a standard Dev Spaces GitLab token Secret. |
| PaC permissions | `pac-bot` needs repo-admin | `pac-bot` is Developer on the GitOps repo; Maintainer on services only to create webhooks |
| Webhooks | One org webhook covers all repos | Per-project webhooks (no group hooks in CE); the registrar creates them |
| "Only the bot merges" | Branch protection allowlist by **user** | By **role**: a separate GitOps group with one Maintainer |
| Required checks | Branch protection status contexts | "Pipelines must succeed" honors PaC external statuses |
| Head-pinned merge | `head_commit_id` → 409 `head out of date` | `sha=` → 409 `SHA does not match HEAD` |
| Recover a failed push run | No commit-comment retrigger | `/retest` on the commit works |
| Token bootstrap | Bot passwords plus a basic-auth token API | Admin API mints tokens for users. The root token is seeded by `gitlab-rails runner`. |

## Final operational state

- **Argo CD app `gitlab`:** Synced/Healthy from `box1-gitops` branch `gitlab-proof`, which is stacked on `forgejo-proof`.
- **Argo CD app `developer-hub`:** synced from `gitlab-proof` (`main` plus the Forgejo and GitLab additions).
- **Template:** `gitlab-proof-service` is registered from `box1-templates` branch `gitlab-proof`.
- **Hand-made state:** `mike-devspaces/personal-access-token-gitlab-box1` (Dev Spaces GitLab token for `box1-dev`).
- **Running:** `box1-gl-dev/gl-svc` and the Dev Spaces workspace `gl-svc`.
- **Empty project left over:** `box1-gl/gl-proof`, from the attempt whose initial push was refused. Nothing ran from it.
- **Cluster:** the node is at 83% memory used. All 58 Argo CD applications are Healthy, and the Forgejo lane still serves.

## Recovery

| What to undo | How |
|---|---|
| Whole GitLab lane | Delete the Argo CD apps `gitlab-proof-workloads` and `gitlab` (prune removes the namespaces `gitlab`, `box1-gl-ci` and `box1-gl-dev`). Then delete `openshift-gitops/gitlab-repo-creds`, `rhdh/developer-hub-gitlab-secrets` and `mike-devspaces/personal-access-token-gitlab-box1`. |
| RHDH | Sync `developer-hub` to the branch you want. The GitLab parts are additive. |
| GitLab data | Lives only on PVC `gitlab/gitlab-data`. There is no backup (**not tested**). |

## Gaps

These carry over from [#167](https://github.com/box1-org/box1-docs/issues/167), adjusted for GitLab:
- The onboarding plugin is GitHub-only.
- The registrar is still needed, now also for webhooks.
- `anyuid` is required.
- Host names are not parameterized.
- The RHPDS replay and backup/restore are **not tested**.

GitLab removes three Forgejo gaps:
- the Dev Spaces factory workaround
- the unbundled RHDH module and its `repoContentsUrl` bug
- `pac-bot` repo-admin on the GitOps repo
