# OpenShift AI removal — 2026-11-09

**Window:** 2026-11-09, about 08:55–09:06 EST (America/New_York)
**Related:** [CPU request right-sizing](2026-11-09-cpu-request-rightsizing.md) (same morning) · original setup and validation: [box1-docs#2](https://github.com/box1-org/box1-docs/issues/2)

## Outcome

Red Hat OpenShift AI 3.4.2 is **fully uninstalled** from Box1 and removed from GitOps. The decision is that Box1 will not run OpenShift AI unless a profile or a concrete use case adopts it. The removal freed **3,200m of CPU requests**, taking node requests from 24,319m (77%) to 21,119m (67%). Nothing else on the cluster depended on it.

## Starting baseline

What was still installed:
- **Operator:** `rhods-operator.3.4.2` from channel `stable-3.4`, with manual InstallPlan approval. It ran three replicas at 500m each.
- **Ownership:** the Argo CD Application `openshift-ai-operator` managed the Namespace, OperatorGroup and Subscription. It synced manually and was discovered by `box1-root`.
- **`DSCInitialization/default-dsci`** and the singletons the operator created from it:
  - Auth, GatewayConfig and Monitoring
  - `OdhDashboardConfig`
  - a default HardwareProfile
  - a ClusterStorageContainer
- **Gateway objects in `openshift-ingress`**, all created by the GatewayConfig:
  - the `data-science-gateway` Gateway and GatewayClass, plus its Envoy deployment (100m)
  - `kube-auth-proxy` ×2 (1,000m)
  - an `oauth-callback-route` HTTPRoute
  - the routes `rh-ai.apps.ocp.box1.org` and `data-science-gateway.apps.ocp.box1.org`
  - `istiod-openshift-gateway` (500m), started by OpenShift's Gateway API controller for that GatewayClass
- **Other leftovers:**
  - `dashboard-redirect` ×2 in `redhat-ods-applications`
  - 39 CRDs and 18 admission webhooks
  - the namespaces `redhat-ods-applications`, `redhat-ods-monitoring`, `rhods-notebooks` and `rhoai-model-registries`

**No AI data remained.** There was no `DataScienceCluster`, so no workbenches, KServe models or pipelines were running. The `box1-ai-test` project and its PVC and ObjectBucketClaim were already gone, so no backup was needed.

**Dependencies checked before removal:**
- `vllm/vllm-test` is a plain Deployment running the upstream `vllm/vllm-openai:v0.28.0` image, with no owner and no KServe objects.
- Lightspeed's provider type `rhoai_vllm` is only a client setting.
- The service-mesh waypoints in the `*-dev` namespaces use the separate `istio-system` ambient control plane.
- cert-manager, Service Mesh, NooBaa, LVMS and the GPU were left untouched.

## What changed

**GitOps.** [box1-gitops#138](https://github.com/box1-org/box1-gitops/pull/138) was squash-merged as `7ad14af` at 09:04 EST. It:
- deleted `applications/openshift-ai-operator.yaml` and the 22 files under `platform/openshift-ai/`, including the validation notebook
- removed the root README entry and added a note naming `7a1da45:platform/openshift-ai/` as the restore point
- dropped the `openshift-ai` tag from the vLLM catalog entry

`box1-root` self-heals but does not prune. The `openshift-ai-operator` Application was therefore deleted by hand after the merge. It had no finalizer, so the delete did not cascade.

**Cluster, in order:**
1. **Red Hat's uninstall trigger.** A ConfigMap `delete-self-managed-odh` was created in `redhat-ods-operator` and labelled `api.openshift.com/addon-managed-odh-delete=true`. Within about 30 seconds the operator had removed:
   - `default-dsci`
   - the `redhat-ods-applications`, `redhat-ods-monitoring` and `rhods-notebooks` namespaces
   - the GatewayClass, Gateway, `kube-auth-proxy` and routes
   - its own Subscription

   `istiod-openshift-gateway` also disappeared once the GatewayClass was gone.
2. **Operator.** The CSV `rhods-operator.3.4.2` and the `redhat-ods-operator` namespace were deleted.
3. **Leftovers removed by hand:**
   - Two operator-created webhooks still pointed at deleted services:
     - `odh-notebook-controller-validating-webhook-configuration`
     - `mutating.odh-model-controller.opendatahub.io`

     Both used `failurePolicy: Fail`, and the second had a rule matching pods. No ReplicaSet reported a creation failure while they were orphaned.
   - The `Auth/auth` and `ClusterStorageContainer/default` singletons.
   - The `kube-auth-proxy` NetworkPolicy and ServiceAccount in `openshift-ingress`.
   - The empty `rhoai-model-registries` namespace.
   - All 39 OpenShift AI CRDs. About 150 aggregate ClusterRoles were owned by them and were garbage-collected.
   - An orphaned `model-catalog-auth-delegator` ClusterRoleBinding. It granted `system:auth-delegator` to a service account in the deleted namespace.

Red Hat's documented procedure leaves the CRDs in place. They were deleted here at the user's direction. A full uninstall had never been tested on this lab before, and these steps are one-way: undoing them means reinstalling.

## Validation and evidence

- **Nothing left behind:**
  - No CRDs remained in the `opendatahub.io`, `kserve.io`, `kubeflow.org`, `llamastack.io` or `nim.opendatahub.io` groups.
  - No OpenShift AI webhooks or OpenShift AI-labelled cluster RBAC remained.
  - No namespaces or routes matching `ods`, `rhoai`, `rh-ai` or `data-science` remained.
  - `openshift-ingress` runs only `router-default`.
- **Health:**
  - All cluster operators were Available and not Degraded.
  - `box1-root` and every other Application were Synced/Healthy at `7ad14af`.
  - No pod newly entered a non-running state compared with the pre-removal baseline.
- **Pod admission:** a throwaway pod in `mike-sandbox` (`ubi9/ubi-minimal`, `/bin/true`) was admitted and reached `Succeeded`, then was deleted.
- **Neighbouring services:** Lightspeed `OLSConfig` stayed `Ready`, and `vllm/vllm-test` stayed 1/1.
- **CPU:** node requests went from 24,319m to **21,119m**.
- **Recorded:** the removal is noted on [box1-docs#2](https://github.com/box1-org/box1-docs/issues/2#issuecomment-6742018008).

## Final operational state

- OpenShift AI is absent from both the cluster and `box1-gitops` `main`. There is no deliberate drift.
- The shared operators it used remain installed and unchanged: cert-manager 1.20.1, Service Mesh 3.5.0, ODF/NooBaa and LVMS.
- The RHDH catalog entry for vLLM no longer carries the `openshift-ai` tag.

## Recovery and follow-ups

- **Reinstall (not tested):** restore `applications/openshift-ai-operator.yaml` and `platform/openshift-ai/` from `7a1da45`, then follow the installation order in that README:
  1. Sync the operator Application and approve the InstallPlan.
  2. Apply the DSCI and DSC.
  3. Bootstrap the test namespace, OBC and connection Secret.

  Prerequisites: channel `stable-3.4` must still be in the catalog, and the platform version gap must be re-checked. OpenShift 5.0 was never on Red Hat's support matrix for this release.
- **No backlog follow-up.** Re-adoption waits on a profile or use case.
