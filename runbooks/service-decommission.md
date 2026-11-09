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

## Virtual machines (`virtual-machine` and `vm-instance` profiles)

Added 2026-11-09 (America/New_York) for
[#138](https://github.com/box1-org/box1-docs/issues/138). Steps 1–6 above still apply,
with the differences below. **Not yet exercised on the cluster**: no VM workload has been
decommissioned with this section. Deleting a VM, a DataVolume or a Secret needs approval.

Find the profile first. It is the `box1.org/workload-profile` label of
`workloads/<name>/namespace.yaml`:

- `virtual-machine` (template `rhel-image-vm`): a VM **with** its own source repository,
  OS image and install disk (for example `legacy-erp`, `vm-golden-check`). It may be the
  **source** of `vm-instance` workloads.
- `vm-instance` (template `vm-instance`): one VM of another repository's OS image. It has
  **no** source repository, no PAC Repository and no image stream of its own.

### Never delete a source that is in use

Before touching a `virtual-machine` workload, check whether it is a source:

```sh
grep -l "box1.org/source-image: <name>$" box1-workloads-dev/workloads/*/virtualmachine.yaml
```

Every instance in that list boots `box1-ci/<name>-disk` and pins `box1-ci/<name>@sha256:…`.
While any instance, or the source VM itself, uses them:

- do **not** delete the `box1-ci/<name>` or `box1-ci/<name>-disk` image streams or their
  tags (step 5), the `box1-ci/<name>:<channel>` tags, or the source repository (step 4);
- decommission or re-point the instances first. Removing `<name>` from
  `VM_INSTANCE_SOURCES` in `box1-gitops` `platform/pipelines/tasks/gitops-validate.yaml`
  makes every remaining instance fail `box1-gitops-validate`, so do it last.

Decommissioning an **instance** never touches the source's image streams, tags,
repository, workload or Application, or another instance.

### What the cascade removes, and what it does not

Step 2 (Application deleted with the resources finalizer) removes what the Application
manages: the namespace and everything in it, plus the out-of-namespace RBAC in the
bundle. For a VM that is:

| Resource | Where | Removed by the step 2 cascade? |
| --- | --- | --- |
| VirtualMachine `<name>` and its VMI, virt-launcher pod | `<name>-dev` | Yes (namespace) |
| DataVolume `<name>-root` and the root PVC (`lvms-vg1`, reclaim `Delete`, so the PV and its logical volume are destroyed) | `<name>-dev` | Yes (namespace). The guest disk is lost; back up first if it matters |
| Data PVCs with `argocd.argoproj.io/sync-options: Prune=false,Delete=false` (today only `legacy-erp-data` in `legacy-erp/erp-data.yaml`) | `<name>-dev` | Argo does not delete them, but deleting the namespace does. Copy the data out before step 2 if it must survive |
| `<name>-updater` ServiceAccount, `<name>-updater-token`, `<name>-admin-ssh` (and `legacy-erp-deploy-ssh`) | `<name>-dev` | Yes (namespace) |
| `<name>-site` ConfigMap (`vm-instance`) | `<name>-dev` | Yes (namespace) |
| `<name>-cloud-init` Secret (`vm-instance`; created **outside Git**, not managed by Argo) | `<name>-dev` | Yes, but only because the namespace goes. Check it is gone |
| `<name>-release-observer`, `<name>-cloud-init-observer`, `<name>-status-reader`, `<name>-deployer` Roles and bindings | `<name>-dev` | Yes (namespace) |
| `<name>-release-observer` Role and RoleBinding | `openshift-gitops` | Yes (managed by the Application). Verify |
| `<name>-image-puller` RoleBinding (Group `system:serviceaccounts:<name>-dev`) | `box1-ci` | Yes (managed by the Application). Verify; a leftover binding would grant pulls to any future namespace of that name |
| PAC Repository `<name>` (`virtual-machine` only) | `box1-ci` | Yes, after the finalizer step above |
| Catalog Location, onboarding ConfigMap and Lease | RHDH, `rhdh` | No: step 3 |
| Image streams `<name>`, `<name>-disk` and PipelineRuns (`virtual-machine` only) | `box1-ci` | No: step 5, and only if no instance uses them |
| `onb-<name>-boot-*` booted-digest PipelineRuns (`vm-instance`) | `box1-ci` | No: step 5 (`-l backstage.io/kubernetes-id=<name>`) |

If the namespace sticks in `Terminating`, look for a VMI or DataVolume finalizer and wait
for virt-controller and CDI before forcing anything.

### `vm-instance` specifics

- **Catalog (step 3):** the Location target is
  `https://github.com/box1-org/box1-workloads-dev/blob/main/workloads/<name>/catalog-info.yaml`,
  not a repository of its own. Delete that Location; then
  `GET /api/catalog/entities/by-name/component/default/<name>` must return 404. There is no
  API entity.
- **Repository (step 4):** none. Skip it.
- **CI leftovers (step 5):** only the `onb-<name>-boot-*` PipelineRuns. Never the source's
  image streams.
- **Credentials:** disable or delete the site's Keycloak client (#131) so the credential in
  the deleted Secret, and in any guest copy, stops working. Deleting the VM does not revoke it.
- **Verify the source and the other instances, before and after:** record
  `box1.org/os-image-digest` of each remaining instance and of the source,
  `oc get is <source> <source>-disk -n box1-ci`, and that their Applications stay
  `Synced`/`Healthy` and their VMs `Ready`.

Example inventory for an instance (read-only):

```sh
NAME=site-west NS=site-west-dev
oc get vm,vmi,dv,pvc,configmap,secret,sa,role,rolebinding -n $NS
oc get rolebinding $NAME-image-puller -n box1-ci
oc get role,rolebinding $NAME-release-observer -n openshift-gitops
oc get pipelineruns -n box1-ci -l backstage.io/kubernetes-id=$NAME
oc get configmap,lease box1-onboard-$NAME -n rhdh
```

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

## Box1 execution on 2026-11-08

Scope: `demo-day`, a Quarkus golden-path demo service. Its Dev Spaces PR
(`demo-day#2`) was retired instead of merged while closing
[#114](https://github.com/box1-org/box1-docs/issues/114).

- **GitOps:** [`box1-workloads-dev#194`](https://github.com/box1-org/box1-workloads-dev/pull/194)
  merged as `937ccb3a79da39a0762bb504c27fef7745f3d160` with both checks passing.
- **Cluster:** after the parent showed the commit and `demo-day` as
  `requiresPruning`, the Application was deleted with the resources finalizer.
  `demo-day-dev` was gone in about 45 seconds, together with the 5Gi
  `demo-day-postgres-data` PVC and its PV, which was destroyed without a backup
  at the owner's direction. The PAC Repository stopped on `foregroundDeletion`
  as described above. It had no dependents, so its finalizer was cleared. No
  release-observer RBAC remains.
- **RHDH:** the onboarding ConfigMap and Lease were deleted. The catalog had a
  location for `https://github.com/box1-org/demo-day/tree/main/catalog-info.yaml`.
  Deleting it returned 204, and both entity lookups then returned 404 before
  the repository was deleted, and again after it.
- **CI leftovers:** the `demo-day` image stream and 3 PipelineRuns (with their
  pods) were deleted from `box1-ci`. Nothing named `demo-day` remains there.
- **GitHub:** `box1-org/demo-day` was deleted at 21:03 EST and returns 404. The
  open `demo-day#2` went with it. Afterwards `box1-workloads-dev` was `Synced` and `Healthy`.

**Calling the catalog API.** The `box1-automation` external-access entry is
a `legacy` token. The token is an HS256 JWT signed with `BACKEND_SECRET`, decoded
as base64 the way Node does it, which is lenient. Its `sub` claim must be
`backstage-server`. The configured `subject` only names the principal. Any
other `sub` returns 401. Keep the token short-lived and never print it.
