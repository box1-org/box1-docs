# OSSM 3.5 and Kiali operators: delivery and coexistence (2026-11-06 America/New_York)

**Change:** [box1-gitops#94](https://github.com/box1-org/box1-gitops/pull/94), squash-merged at the user's instruction as `9738e5b`. The Argo Application `service-mesh-operators` was synced at 21:58:16 EST (operation at that revision) and reported `Succeeded`.

**InstallPlans, inspected before approval:**
- `openshift-service-mesh-operator/install-zf556` (`servicemeshoperator3.v3.5.0`) has 31 steps:
  - 20 CRDs: the 15 `*.istio.io` CRDs the ingress operator owned, plus 5 `sailoperator.io` CRDs;
  - 2 ClusterRoles and 2 ClusterRoleBindings, 1 Role and 1 RoleBinding, a ServiceAccount, a Service, a ServiceMonitor and a ConsoleCLIDownload.
- `openshift-kiali-operator/install-r22q8` (`kiali-operator.v2.33.1`) creates `kialis.kiali.io` and `ossmconsoles.kiali.io`, a ClusterRole and binding, and a ServiceAccount.
- Both were approved at 21:59:18. Both CSVs were `Succeeded` by 22:00:11, and both operator pods are Running 1/1.

**Why taking over the CRDs was judged safe:** the ingress operator source (`openshift/cluster-ingress-operator`, `pkg/operator/controller/gatewayclass/istio_sail_installer.go`, `overwriteOLMManagedCRDFunc`) leaves a CRD alone when it is `olm.managed` and an OLM Subscription or InstallPlan exists for it. If looking that up fails, it also leaves the CRD alone.

**Observed coexistence:**
- **14 of the 15 `*.istio.io` CRDs** now carry `olm.managed=true` and `operators.coreos.com/servicemeshoperator3.openshift-service-mesh-operator`. The ingress label is gone.
- **`gateways.networking.istio.io` went back to the ingress operator.** At 02:59:21Z it logged `no subscription label found` for that CRD. OLM had applied it before adding the subscription label, and the ingress operator rewrote it in that window.
  - It is Istio's classic `Gateway` API, which ambient and waypoints do not use; waypoints use Gateway API `gateway.networking.k8s.io`.
  - Its served versions are unchanged, and the CSV is `Succeeded`.
- The ingress operator logs `error trying to get subscription … unknown namespace for the cache`. Its cache does not watch `openshift-service-mesh-operator`, and in that case it does not overwrite.
- **No ownership fight:** over 120 s (22:01:41–22:03:41) no `*.istio.io` CRD resourceVersion changed, and the ingress operator logged no overwrite messages.
- `istiod-openshift-gateway` is 1/1 with no restart. `data-science-gateway-class` is Accepted. The `ingress` cluster operator is Available.
- No `Istio`, `IstioRevision`, `IstioCNI` or `ZTunnel` exists yet.

**Versions now available:** `istios.sailoperator.io` v1 accepts `v1.26`–`v1.31`, default `v1.31.1`. The ingress istiod runs `1.30.4_ossm`. Kiali CRD `v1alpha1`.

**Limitations:**
- `gateways.networking.istio.io` is owned differently from the other 14 CRDs. If an OSSM upgrade changes that CRD, the ingress operator may keep its own version. It is not used by this run.
- OSSM support on OpenShift 5.0 rc is **not established**.
