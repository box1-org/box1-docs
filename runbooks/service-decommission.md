# Box1 service decommissioning

Use this runbook when retiring a Box1 application created through the Golden
Path. The order matters: remove the declarative deployment first, remove the
catalog registration, and delete the source repository last. Do not delete a
repository while an Argo Application still points at it or while a release or
onboarding operation is active.

## Required inputs

- service name and source repository (`box1-org/<service>`)
- the owning GitOps workload path (`workloads/<service>`) and Application
  manifest (`applications/<service>.yaml`)
- the RHDH component and API entity refs (`component:default/<service>` and
  `api:default/<service>-api`)
- approval to delete the GitHub repository; repository deletion is irreversible

## Procedure

1. Inventory the source repository, open pull requests, GitOps Application,
   workload directory, RHDH catalog location, onboarding ConfigMap and Lease.
   Stop or wait for active releases before continuing.
2. In `box1-workloads-dev`, remove `applications/<service>.yaml` and the entire
   `workloads/<service>/` directory in a reviewed pull request. Merge only after
   `box1-gitops-validate` and `box1-phase1-smoke` pass.

   Merging does not remove anything from the cluster. The parent Application
   `box1-workloads-dev` has `selfHeal` but not `prune`, and child Applications
   have no resources finalizer, so they stay deployed and only show as
   `requiresPruning`. Hard-refresh the parent and confirm it is on the merge
   commit, because deleting a child earlier lets `selfHeal` recreate it. Then
   add the finalizer and delete the Application:

   ```sh
   kubectl -n openshift-gitops annotate application box1-workloads-dev \
     argocd.argoproj.io/refresh=hard --overwrite
   kubectl -n openshift-gitops patch application <service> --type=merge \
     -p '{"metadata":{"finalizers":["resources-finalizer.argocd.argoproj.io"]}}'
   kubectl -n openshift-gitops delete application <service> --wait=false
   ```

   This cascade destroys the namespace and any PostgreSQL volume in it. Back up
   first if the data matters.

   The Application then hangs on its PAC Repository in `box1-ci`, which stays on
   the `foregroundDeletion` finalizer. The Pipelines as Code admission webhook
   rejects the garbage collector's update because that service account cannot
   create PipelineRuns there. Confirm the Repository has a `deletionTimestamp`
   and no dependents, then clear the finalizer as a user who can create
   PipelineRuns in `box1-ci`:

   ```sh
   kubectl -n box1-ci patch repositories.pipelinesascode.tekton.dev <service> \
     --type=merge -p '{"metadata":{"finalizers":null}}'
   ```

   Verify the Application, namespace, Repository and release-observer RBAC are
   gone before deleting the source repository. `DeletionError` conditions that
   name resources in the already-deleted namespace cleared once the Repository
   was gone.
3. Remove the RHDH catalog location. RHDH's onboarding plugin adds a URL
   location for `https://github.com/box1-org/<service>/tree/main/catalog-info.yaml`;
   deleting the repository alone does not guarantee immediate removal of this
   location. Not every service has one: GitHub discovery also registers
   components, so an entity with no location of its own can return 200 until
   the repository is deleted. From a maintenance shell with the RHDH backend credential, list
   `GET /api/catalog/locations`, find that exact target, and issue
   `DELETE /api/catalog/locations/<id>`. Confirm both catalog entity lookups
   return 404:

   ```text
   GET /api/catalog/entities/by-name/component/default/<service>
   GET /api/catalog/entities/by-name/api/default/<service>-api
   ```

   Run these lookups again after step 4, and treat that second check as the
   final one for discovered entities.

   Also remove the onboarding state records after the workflow is no longer
   running:

   ```sh
   kubectl -n rhdh delete configmap box1-onboard-<service> --ignore-not-found
   kubectl -n rhdh delete lease box1-onboard-<service> --ignore-not-found
   ```

4. Delete the GitHub repository only after steps 1–3 are verified:

   ```sh
   gh repo delete box1-org/<service> --yes
   ```

   Record the deletion date, the final GitOps merge commit, and the RHDH
   entity/location verification in the achievement log. If policy blocks
   deletion, archive the repository and leave the source URL in the exception
   record instead of claiming deletion.
5. Remove CI leftovers from `box1-ci`: the service's image stream, and its
   PipelineRuns, including the `onb-<service>-*` onboarding runs and any
   manually created runs:

   ```sh
   kubectl -n box1-ci delete imagestream <service> --ignore-not-found
   kubectl -n box1-ci delete pipelineruns -l backstage.io/kubernetes-id=<service>
   ```

   Also delete any `<run>-git` secrets those runs left behind. Deleting the
   image stream removes the last in-cluster reference to the built images.
6. Search `box1-gitops`, `box1-workloads-dev`, `box1-templates`, and
   `box1-docs` for the service name. Remove operational links and live-check
   scripts, but retain historical evidence with a clear `retired` label and a
   link to this runbook.

## Box1 execution on 2026-10-26

The four requested services were:

- `football-service` (requested commit `3cf86ad`)
- `orders-service` (requested commit `c511ea3`)
- `shipping-service` (requested commit `4108bd2`)
- `quarkus-golden-path-smoke` (requested commit `257ac0f`)

The GitOps deletion merged in
[`box1-workloads-dev#10`](https://github.com/box1-org/box1-workloads-dev/pull/10)
as commit `25a3c3f62379bf28c9c33a3197aea57b013454d2`, removing all four Argo
Applications and their workload/onboarding manifests. Cluster prune and
namespace deletion were **not verified** because the configured Box1 API
hostname did not resolve from the workstation.

GitHub repository deletion was requested but blocked by the execution safety
review because it is irreversible. The repositories therefore remain until an
authorized operator performs the `gh repo delete` step. RHDH catalog-location
and onboarding-state deletion were also not performed because
`developer-hub.apps.ocp.box1.org` and `api.ocp.box1.org` were unreachable.

Do not mark this decommission complete until the repository deletion, RHDH
entity 404 checks, and cluster prune verification have durable evidence.

## Box1 execution on 2026-11-05

Scope: 17 Golden Path services in `box1-workloads-dev`, plus `al-service` and
`hammer-service`, which had repositories and catalog entries but no Application
or namespace. `quarkus-reference` was deliberately kept because `box1-gitops`
`pipelines-ci`, the Tekton task defaults and the RHDH verify scripts depend on it.

Removed: `atrioc-service`, `blue-wave`, `bypass-service`, `ds9`, `enterprise`,
`gold-service`, `halloween-service`, `hammer2-service`, `hammer3-service`,
`morgan-service`, `post-show`, `smallville-service`, `test-service`, `tng`,
`trash-service`, `voyager`, `world-series-service`, `al-service`,
`hammer-service`.

- **GitOps:** [`box1-workloads-dev#47`](https://github.com/box1-org/box1-workloads-dev/pull/47)
  merged as `9004149924668e5c94961a991e276cb80c6632f1` with both checks passing.
- **Cluster:** all 17 Applications, namespaces and PAC Repositories are gone. 21
  Argo Applications and 4 PAC Repositories remain, as expected. No PersistentVolumes
  remain for these namespaces. Nine 5Gi PostgreSQL volumes were destroyed
  without a backup, at the owner's direction.
- **RHDH:** 12 catalog locations and all 19 onboarding ConfigMaps and Leases were
  deleted. The catalog now holds only `component:default/quarkus-reference` and
  `api:default/quarkus-reference-api`. Discovered entities cleared within about
  three minutes of repository deletion, not on the 30-minute scan. Why they
  cleared that quickly was not established.
- **GitHub:** all 19 repositories were deleted at about 01:37 EST and each returns
  HTTP 404. Open pull requests `atrioc-service#1` and `world-series-service#1`
  went with them.
- **After removal:** `quarkus-reference` and `box1-workloads-dev` are `Synced` and
  `Healthy`, and the `quarkus-reference` health endpoint and the Hub return 200.

CI leftovers were removed the same night: 12 image streams, 21 PipelineRuns (with
their TaskRuns and Pods) and 4 `atrioc-observe-*-git` secrets in `box1-ci`. The
image streams for the October services (`football-service`, `orders-service`,
`shipping-service`, `quarkus-golden-path-smoke`) were left in place.

**Update on the 2026-10-26 execution above:** on 2026-11-05 those four
repositories returned 404, their namespaces were absent, and the catalog held
no entries or locations for them. When and by whom they were removed is not
recorded here.

The onboarding plugin is not re-tested by this cleanup. Service names in earlier
achievement logs are historical; those repositories no longer exist.
