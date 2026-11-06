# Backup of manually created Box1 objects

This directory holds cleaned YAML exports of the objects listed in
[`../manual-installs-and-secrets.md`](../manual-installs-and-secrets.md).
Those objects were created by hand, not by Argo CD or an operator. Use the
exports as source material when you rebuild them or move them into
`box1-gitops`.

- **Exported:** 2026-11-05 America/New_York, OpenShift 5.0.0-rc.7, read-only
  `oc get`
- **Generator:** [`dump.py`](dump.py). Run it with
  `python -I dump.py manual/backup`; it needs PyYAML and a logged-in `oc`
  session.
- **Validation:** every file passed `oc apply --dry-run=server` against the
  live cluster except `secrets/box1-ci.yaml`. That file fails on purpose,
  because a placeholder is not valid `.dockerconfigjson` JSON.

## What "cleaned" means

The script removed or redacted the following:

- `status`, plus the metadata fields `uid`, `resourceVersion`, `generation`,
  `creationTimestamp`, `managedFields`, `ownerReferences` and `finalizers`.
- Controller-written labels and annotations: OLM, pod-security sync, SCC
  ranges, `last-applied-configuration`, deployment revision, cert-manager,
  release/capability, and Argo CD tracking.
- Values assigned at runtime: Service cluster IPs, generated Route hosts, PVC
  `volumeName`, ServiceAccount token references, and ImageStream tag
  generations.
- **Secrets:** each `data` field was replaced with `stringData` whose keys are
  kept and whose values read `<REDACTED: supply value out of band>`. The
  `last-applied-configuration` annotation, which embeds plaintext data, was
  removed.
- **Workloads:** container env values whose names suggest credentials were
  replaced with `<REDACTED>`. None of the exported Deployments had one.
  BuildConfig webhook trigger secrets were also redacted.

Default fields that the API server fills in (for example `HyperConverged`
feature gates, ODF `StorageCluster` settings and Deployment
`terminationMessagePath`) were kept. Review them before you reuse a manifest in
GitOps, and trim whatever you don't intend to pin.

## Layout

| Path | Contents |
| --- | --- |
| `operators/` | Namespace, OperatorGroup and Subscription for each manually installed operator, plus the two manual CatalogSources. `web-terminal.yaml` holds only the Subscription; it uses the cluster-default `openshift-operators` group. |
| `operands/` | `ClusterPolicy`, `NodeFeatureDiscovery`, `LVMCluster`, `StorageCluster` and `HyperConverged` |
| `cluster-config/` | `KubeletConfig`, the two console MachineConfigs, the ClusterIssuer and API/apps Certificates, `OAuth`, `APIServer` and the default `IngressController` |
| `workloads/` | agent-sandbox controller (Namespace, CRD, RBAC, Service, Deployment), `vllm-test` and `inventory-poc` |
| `secrets/` | **Redacted templates**, one file per namespace |

Not included:

- **The OpenShell Helm release** (chart `helm-chart` 0.1.5, revision 4). Its
  values contain no credentials; recover them with
  `helm get values openshell -n openshell`. Its key Secrets are in
  `secrets/openshell.yaml`.
- **Argo-managed objects.** Their source is already in Git.
- **Installer-created secrets**, such as `pull-secret` and `kubeadmin`.

## Restoring

> **Do not run `oc apply -R -f manual/backup/`.** The Secret templates pass
> server validation, so applying them unfilled would replace live credentials
> with placeholder text.

1. Restore in the order in the runbook's *Rebuild order* section. Apply
   `operators/`, wait for the CSVs to reach `Succeeded`, then apply
   `operands/` and `cluster-config/`.
2. For each Secret, copy the template outside the repository and fill every
   value from its secure source. The runbook table names the source. Then
   apply the filled copy. Never commit a filled copy.
3. Subscriptions with `installPlanApproval: Manual` (GitOps, NVIDIA GPU and
   LVMS) need their InstallPlan approved. Each `startingCSV` pins the version
   that was installed at export time.
4. `HyperConverged` and `StorageCluster` contain cluster-specific device and
   storage settings, so check them against the rebuilt hardware before you
   apply them.

None of these restore steps have been exercised.
