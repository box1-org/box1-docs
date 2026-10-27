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
   `box1-gitops-validate` and `box1-phase1-smoke` pass. Argo CD then prunes the
   Application's namespace-scoped resources. Verify the Application is gone and
   the namespace, Deployment, Service, Route, ServiceAccount and RBAC objects
   are absent before deleting the source repository.
3. Remove the RHDH catalog location. RHDH's onboarding plugin adds a URL
   location for `https://github.com/box1-org/<service>/tree/main/catalog-info.yaml`;
   deleting the repository alone does not guarantee immediate removal of this
   location. From a maintenance shell with the RHDH backend credential, list
   `GET /api/catalog/locations`, find that exact target, and issue
   `DELETE /api/catalog/locations/<id>`. Confirm both catalog entity lookups
   return 404:

   ```text
   GET /api/catalog/entities/by-name/component/default/<service>
   GET /api/catalog/entities/by-name/api/default/<service>-api
   ```

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
5. Search `box1-gitops`, `box1-workloads-dev`, `box1-templates`, and
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
