# demo-day decommissioned

**Date:** 2026-11-08 (America/New_York), 20:57–21:05 EST.

**Status:** Complete. The step-by-step record is the 2026-11-08 section of [`runbooks/service-decommission.md`](https://github.com/box1-org/box1-docs/blob/main/runbooks/service-decommission.md); this entry summarizes it.

## Outcome and purpose

`demo-day`, a Quarkus golden-path demo service, is gone from GitOps, the cluster, Developer Hub, CI and GitHub. The user chose to retire it rather than merge its Dev Spaces PR (`demo-day#2`), which was the last open item in the Dev Spaces rollout ([#114](https://github.com/box1-org/box1-docs/issues/114), see [2026-11-08-dev-spaces-developer-environment.md](2026-11-08-dev-spaces-developer-environment.md)).

## Starting baseline

- Argo app `demo-day` `Synced`/`Healthy`; namespace `demo-day-dev` with the app and PostgreSQL running and a 5Gi `demo-day-postgres-data` PVC (reclaim policy `Delete`).
- PAC Repository `demo-day` in `box1-ci`, image stream `demo-day`, 3 PipelineRuns.
- Onboarding ConfigMap and Lease `box1-onboard-demo-day` in `rhdh` (phase `COMPLETE`); a catalog location for the repository's `catalog-info.yaml`.
- Repository `box1-org/demo-day` with one open PR, `demo-day#2`.

## What changed

- **GitOps:** [box1-workloads-dev#194](https://github.com/box1-org/box1-workloads-dev/pull/194) removed `applications/demo-day.yaml` and `workloads/demo-day/`. Merged as `937ccb3` after both checks passed.
- **Cluster:** after the parent app showed the merge commit and `demo-day` as `requiresPruning`, the Application was deleted with the resources finalizer. The PostgreSQL volume was destroyed **without a backup, at the user's direction**. The PAC Repository stopped on `foregroundDeletion` as the runbook predicts; it had no dependents, so its finalizer was cleared.
- **Developer Hub:** the catalog location was deleted through the catalog API (204), and the onboarding ConfigMap and Lease were removed.
- **CI:** the image stream and 3 PipelineRuns (with their pods) were deleted from `box1-ci`.
- **GitHub:** `box1-org/demo-day` was deleted at 21:03 EST, taking `demo-day#2` with it. Approved by the user.
- **Docs:** [box1-docs#123](https://github.com/box1-org/box1-docs/pull/123) (`a1d1f5b`) removed demo-day from the README and recorded the run in the runbook.

**Lesson recorded in the runbook:** the catalog API's `legacy` service token must carry `sub: backstage-server`. The configured `subject` only names the principal; any other `sub` gets a 401.

## Validation and evidence

| Check | Result |
|---|---|
| Argo Application, namespace, PVC and PV | All NotFound |
| PAC Repository and release-observer RBAC | NotFound |
| `box1-ci` | No objects named `demo-day` |
| Catalog `component:default/demo-day` and `api:default/demo-day-api` | 404 before and after the repository deletion |
| `GET repos/box1-org/demo-day` | 404 |
| Survivors | `box1-workloads-dev`, `inventory-service` and `order-service` `Synced`/`Healthy` at `937ccb3` |

## Final state and recovery

Nothing remains of demo-day. Earlier achievement logs that mention it are historical. The data and repository can't be recovered; a new service could be created from the golden path under the same name, but reusing the name is **not tested**. No follow-ups.
