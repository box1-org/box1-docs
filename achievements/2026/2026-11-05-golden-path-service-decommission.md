# Golden Path service decommission

**Date:** 2026-11-05 (America/New_York)
**Status:** Complete for the 19 services in scope. The October image streams and one reference cleanup remain, as listed under follow-ups. No backlog issue tracked this work. Procedure: [service decommission runbook](../../runbooks/service-decommission.md).

## Outcome

All 19 test services generated through the Golden Path are gone from Argo CD, the cluster, Developer Hub, `box1-ci` and GitHub. `quarkus-reference` is now the only application deployed through `box1-workloads-dev` and the only service in the catalog.

This is a deliberate clean slate, and most of it cannot be undone: nine PostgreSQL databases were dropped without a backup, and the source repositories and image streams were deleted.

The work also showed that the runbook was wrong about how removal works. It has been corrected.

## Starting baseline

Taken from the cluster and GitHub just before the work:

- `box1-workloads-dev` declared 18 applications. Its namespace of the same name was empty, so "applications in `box1-workloads-dev`" meant the GitOps repository.
- Argo CD had 38 Applications, and `box1-ci` had 21 PAC Repositories. All Applications were `Synced`. `hammer2-service`, `hammer3-service` and `morgan-service` were `Progressing`.
- The catalog had 20 components and 20 APIs, and 13 `url` locations including `quarkus-reference`. `box1-org` had 25 repositories.
- `rhdh` held 19 onboarding records: 11 `COMPLETE` and 8 `FAILED`. None was running.
- Nine services had a 5Gi PostgreSQL volume: `blue-wave`, `enterprise`, `hammer2-service`, `hammer3-service`, `morgan-service`, `post-show`, `tng`, `trash-service`, `voyager`.

## What changed

**Scope, decided by the owner:**

- **Removed from GitOps and the cluster (17):** `atrioc-service`, `blue-wave`, `bypass-service`, `ds9`, `enterprise`, `gold-service`, `halloween-service`, `hammer2-service`, `hammer3-service`, `morgan-service`, `post-show`, `smallville-service`, `test-service`, `tng`, `trash-service`, `voyager`, `world-series-service`.
- **Also removed (2):** `al-service` and `hammer-service`, which had a repository and catalog entries but no Application or namespace.
- **Kept:** `quarkus-reference`, because `pipelines-ci`, the Tekton task defaults and the RHDH verify scripts in `box1-gitops` depend on it, and [box1-docs#8](https://github.com/box1-org/box1-docs/issues/8) names it as a validation target.
- **Data:** dropped without a backup, by owner decision.

**Sequence (EST):**

| Time | Step |
|---|---|
| 01:30 | [box1-workloads-dev#47](https://github.com/box1-org/box1-workloads-dev/pull/47) merged as `9004149`, with `box1-gitops-validate` and `box1-phase1-smoke` passing |
| 01:31 | Parent hard-refreshed; the resources finalizer added to the 17 Applications, which were then deleted |
| about 01:36 | The `foregroundDeletion` finalizer cleared on the 17 PAC Repositories; Applications finished deleting |
| before 01:37 | 12 catalog locations and 19 onboarding ConfigMaps and Leases deleted |
| 01:37 | 19 GitHub repositories deleted |
| 01:43 | `box1-ci` cleanup: 12 image streams, 21 PipelineRuns, 4 secrets |

**Two runbook assumptions were wrong:**

- **Merging does not remove anything.** The parent Application has `selfHeal` without `prune`, and child Applications have no resources finalizer. After the merge, the children only showed as `requiresPruning` and stayed deployed. They were deleted by hand, with the finalizer added first so the delete would cascade.
- **Not every catalog entry has a location.** Only 12 of the 19 services had one. The other 7 stayed in the catalog until their repositories were deleted, because they came from GitHub discovery.

**One workaround was needed.** The Pipelines as Code admission webhook rejects Repository updates from accounts that cannot create PipelineRuns in the namespace. That includes the garbage collector, so Repositories in foreground deletion never finish, and the Applications waited on them. Controller logs showed the denial. After confirming no dependents existed, the finalizer was cleared on those 17 Repositories using the operator's account. The webhook and its permissions were not changed, so any future decommission will hit this too.

## Validation and evidence

| Check | Expected | Observed |
|---|---|---|
| Parent scope after merge | Only the 17 need pruning | 17 `requiresPruning`; `quarkus-reference` `Synced` |
| Cascade reach | Nothing shared | Outside its own namespace, each app owned only its namespace, PAC Repository and own RBAC |
| Argo CD | 21 Applications | 21, all `Synced` and `Healthy` |
| PAC Repositories | 4 | `box1-gitops`, `box1-templates`, `box1-workloads-dev`, `quarkus-reference` |
| Namespaces, PVCs, PVs | None for these services | None |
| Catalog | Only `quarkus-reference` | Catalog API and database show one component and one API; one location remains |
| GitHub | Each repository returns 404 | All 19 return 404; 6 repositories remain in `box1-org` |
| `box1-ci` | No objects for these services | No image streams, PipelineRuns, TaskRuns, Pods, secrets, ConfigMaps or PVCs matched |
| Survivors | Still working | `quarkus-reference` `Synced` and `Healthy`, `/q/health` returned 200; the Hub returned 200; `pipelines-ci` `Synced` and `Healthy` |

**Not tested or not established:**

- No new onboarding ran after the cleanup, so reusing a deleted name is **not tested**.
- No `quarkus-reference` pipeline ran after the cleanup, so CI is **not tested** beyond its Repository and `pipelines-ci` being healthy.
- Why discovered catalog entries cleared in about three minutes, rather than on the 30-minute scan, is **not established**.
- Whether registry storage or LVM capacity was reclaimed is **not verified**.

## Final operational state

- **`box1-workloads-dev`:** `main` at `9004149` declares only `quarkus-reference`. It remains managed by Argo CD and matches `main`.
- **`box1-ci`:** 37 PipelineRuns remain, all from `box1-gitops`, `box1-templates` and `box1-workloads-dev`. Image streams remain for `quarkus-reference` and the four services retired in October.
- **Catalog and repositories:** `quarkus-reference` is the only service in the catalog. `box1-org` holds `box1-docs`, `box1-gitops`, `box1-ops-contracts`, `box1-templates`, `box1-workloads-dev` and `quarkus-reference`.
- **Workarounds left running:** none. The finalizer clearing was a one-off on objects that no longer exist.

## Recovery and follow-ups

Recovery was **not tested**, and a full restore is not possible:

- **Deployments:** reverting #47 restores the manifests, but those manifests reference deleted images.
- **Source and pull requests:** deleted from GitHub, along with open PRs `atrioc-service#1` (the CVE-2022-42889 security-gate negative test) and `world-series-service#1`. GitHub's restore option was not tried. A workstation clone of `atrioc-service` exists but is not a durable copy.
- **Databases:** not recoverable.

The services can be recreated by onboarding them again, as new empty services.

Follow-ups, with no owner assigned and no issue filed:

- Decide whether to delete the image streams for `football-service`, `orders-service`, `shipping-service` and `quarkus-golden-path-smoke`. This cleanup left them alone because they belong to the October retirement.
- Decide whether earlier logs and [box1-docs#32](https://github.com/box1-org/box1-docs/issues/32) need a `retired` label where they name these services. They were not changed, and links to the deleted repositories no longer work.
- Decide whether the parent Application should prune, and whether the PAC webhook should exempt the garbage collector. Either would simplify this runbook. Neither was changed.
- Earlier evidence for the security-gate negative test was held in `atrioc-service` and its PipelineRuns, which are now gone.
