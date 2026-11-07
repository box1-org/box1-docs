# Phase 0 discovery (read-only, 2026-11-06 America/New_York)

No cluster state was changed. Commands: `oc get`, `oc adm top`, `oc auth can-i`. Repositories were read at `box1-gitops` `e07852a`, `box1-workloads-dev` `3c12637`, `box1-docs` `2d0d078`.

## Cluster
- OpenShift `5.0.0-rc.7`, single node `quark.host.box1.org`, OVN-Kubernetes.
- `oc adm top node` (about 21:00 EST): 6,221m CPU (19%), 80,774 MiB (63%).
- OVN `gatewayConfig.routingViaHost: false` (shared gateway mode). IPsec disabled. MTU 1400.
- The cluster is not FIPS-relevant here; ambient is not supported on FIPS clusters (Red Hat release notes). Not checked further.

## Existing Istio: the OpenShift Gateway API controller
- `istiod-openshift-gateway` runs in `openshift-ingress`. Its image is `registry.redhat.io/openshift-service-mesh/istio-pilot-rhel9@sha256:f97057b8…`.
- Its environment:
  - `REVISION=openshift-gateway`;
  - `PILOT_ENABLE_GATEWAY_API_DEPLOYMENT_CONTROLLER=true` and `PILOT_ENABLE_GATEWAY_API_GATEWAYCLASS_CONTROLLER=false`;
  - `PILOT_CA_CERT_CONFIGMAP=openshift-gw-ca-root-cert`, so it does not write `istio-ca-root-cert`, which no namespace has;
  - `CA_TRUSTED_NODE_ACCOUNTS=kube-system/ztunnel`.
- Its mesh config has `rootNamespace: openshift-ingress`, `trustDomain: cluster.local` and `ingressControllerMode: "OFF"`, and no `discoverySelectors`.
- The `*.istio.io` CRDs (served `v1`, `v1alpha3`, `v1beta1`) carry `ingress.operator.openshift.io/owned: "true"` and Helm labels. There is no `sailoperator.io` CRD, and no OSSM, Kiali, ztunnel or Istio CNI CSV or pod.
- GatewayClass `data-science-gateway-class` (controller `openshift.io/gateway-controller/v1`) is Accepted; it comes from RHOAI.
- The Gateway API CRDs are installed by the platform (created 2026-10-22).

## Catalog (`redhat-operators`)
| Package | Default channel → CSV | Other channels | Install modes |
|---|---|---|---|
| `servicemeshoperator3` | `stable` → `v3.5.0` | `stable-3.5` v3.5.0, `stable-3.4` v3.4.4, `stable-3.3` v3.3.9 | AllNamespaces only |
| `kiali-ossm` | `stable` → `kiali-operator.v2.33.1` | `candidate` v2.1.2 | AllNamespaces only |

Vendor support for these on OpenShift 5.0 rc is **not established**. The OSSM 3.5 support table (Kiali and Istio versions) was not retrievable (docs.redhat.com returned 403 to the fetcher).

## Ambient prerequisites found in vendor and upstream sources
- **Local gateway mode is required.** Red Hat's OSSM 3.2 release notes state that liveness and readiness probes of ambient workloads need `routingViaHost: true`. The OSSM 3.3 install prerequisites list it. The OSSM CI script (`openshift-service-mesh/istio`, `prow/integ-suite-ocp.sh`) patches `networks.operator.openshift.io cluster` with it before ambient tests. **This cluster has it `false`.**
- OCP 4.19+ (Gateway API CRDs) and OSSM operator 3.1.0+ are required.
- The Sail docs (`docs/ossm/ambient/README.md`) say ambient next to an existing OSSM installation "is not a scenario we have thoroughly validated". The existing `istiod` here is the ingress operator's Gateway API controller, not an OSSM mesh. **Coexistence with it is not established** by any source found.
- With `discoverySelectors`, label both the `Istio` namespace and the `ZTunnel` namespace before creating the `ZTunnel` (istio/istio#52057).
- `ZTunnel` must be named `default` (cluster-wide singleton).
- Ztunnel metrics under OpenShift monitoring need a PodMonitor in the ztunnel namespace.
- L7 spans come only from waypoints; ztunnel produces L4 data only. Tracing uses a `meshConfig.extensionProviders` OpenTelemetry entry plus a `Telemetry` resource.

## Box1 namespaces and GitOps ownership
- The seven service namespaces are declared in `box1-workloads-dev/workloads/<service>/namespace.yaml`. Their Argo Applications (`applications/<service>.yaml`) auto-sync with `selfHeal: true`. Namespace labels include `pod-security.kubernetes.io/enforce: restricted`.
- Pods per namespace: one service pod plus one Postgres pod each, except `operations-console-dev`, which has only the console. The seven namespaces together use about 83m CPU and about 1.87 GiB memory.
- NetworkPolicies:
  - `<service>-postgres` in six namespaces allows ingress only from the service pod on TCP 5432;
  - `order-service-dev` has its policy in `networkpolicy.yaml`, the others in `postgres.yaml`;
  - `legacy-erp-sftp` allows the adapter pod in `fulfillment-adapter-dev` on 2222, and any source on 22;
  - Strimzi `box1-kafka-network-policy-kafka` leaves 9092 open to everyone;
  - `box1-observability` has collector and Tempo policies.
  - No service namespace has an egress policy.
- Platform Applications in `box1-gitops/applications/` are manual-sync. Operators use `installPlanApproval: Manual` (pattern: `platform/observability/operators/tempo.yaml`).
- The Argo application controller can create ClusterRoles and can patch `networks.operator.openshift.io`. The network operator config is **not** in `box1-gitops`.

## Observability already present (#22)
TempoMonolithic `box1` behind the OpenShift-mode gateway (tenant `dev`); collector `box1-collector.box1-observability.svc:4317/4318` (unauthenticated OTLP in); UWM scraping all seven services; COO 1.5.5 with the `distributed-tracing` UIPlugin; Perses datasource `box1-thanos-querier`.
