# Mesh control plane and Kiali: delivery and verification (2026-11-06 America/New_York)

**Change:** [box1-gitops#95](https://github.com/box1-org/box1-gitops/pull/95), squash-merged at the user's instruction as `b71a407`. Synced at that revision: `service-mesh-control-plane` (22:15), `observability-tracing` (22:17, Kiali → Tempo NetworkPolicy) and `service-mesh-kiali` (22:17). All three are `Synced`; Kiali was `Progressing` until its pod was ready.

**First sync failed once:**
- The `Telemetry` (wave 2) hit istiod's validating webhook before istiod had endpoints. Argo CD has no health check for the `Istio` CR, so the sync waves did not wait.
- A second sync about two minutes later succeeded.
- Follow-up: add `syncPolicy.retry` to the Application, or a health check for `sailoperator.io` kinds.

## Control plane
- `Istio/default` v1.31.1 (ambient): Healthy. `IstioRevision/default`: Ready, `IN USE` False. `IstioCNI/default` and `ZTunnel/default`: Healthy.
- `istiod`, `istio-cni-node` and `ztunnel` are each 1/1 Running, all within about 30 s of the sync.
- No namespace has `istio.io/dataplane-mode=ambient`. `istio-ca-root-cert` exists only in `istio-system` and `ztunnel`, so the discovery selectors work.

## Coexistence with the Gateway API istiod
- `istiod-openshift-gateway` 1/1, not restarted. `data-science-gateway-class` Accepted. `ingress` and `network` cluster operators Available.
- Separate root CA ConfigMaps: `openshift-gw-ca-root-cert` (openshift-ingress) and `istio-ca-root-cert` (mesh namespaces).
- CRD ownership unchanged from `phase6-operators.md`: 14 OLM-managed, 1 ingress-owned.
- **New cluster-scoped objects from this istiod:**
  - GatewayClasses `istio`, `istio-remote` and `istio-waypoint`;
  - webhooks `istio-sidecar-injector`, `istio-validator-istio-system` and `istiod-default-validator`.
  - The injector matches only namespaces labelled `istio-injection`/`istio.io/rev`, or pods labelled for injection. No such namespace or pod exists, so no sidecars are injected.

## Metrics (Thanos Querier, user-workload monitoring)
- `up{namespace="ztunnel"}` = 1 (PodMonitor `ztunnel`, port 15020).
- `up{namespace="istio-system"}` = 1 (ServiceMonitor `istiod`).
- istiod xDS metrics are present.

## Kiali (`https://kiali-istio-system.apps.ocp.box1.org`)
- **Anonymous:** `GET /api/namespaces` → 401. `/` serves the login page.
- **Authenticated** (cluster-admin token): namespaces = `istio-system`, `ztunnel` only, matching the discovery selector.
- `/api/istio/status`: istiod, prometheus, tracing and custom dashboards all `Healthy`. Tempo reports 2.10.10 through the gateway (tenant `dev`), and Prometheus is connected.
- Logs: warnings only for optional CA-bundle files.
- **Not verified:** a browser OAuth login; a non-admin user's view.

## Resource cost (22:18 EST, before any enrollment)
| Pod | CPU used | Memory used | Requests |
|---|---|---|---|
| istiod | 2m | 178Mi | 100m / 512Mi |
| kiali | 3m | 42Mi | 20m / 128Mi |
| istio-cni-node | 1m | 99Mi | 100m / 100Mi |
| ztunnel | 1m | 4Mi | 200m / 512Mi |
| OSSM operator | 2m | 335Mi | 10m / 64Mi |
| Kiali operator | 2m | 548Mi | 10m / 64Mi |
| **Total** | **11m** | **about 1.2 GiB** | **440m / about 1.4 GiB** |

Node: 3,716m (11%) and 82,935Mi (64%). Before the sync it was 6,027m and 85,334Mi; normal variation is larger than the mesh's cost.

## Business flow
Order `ord_91faa76ec57445f194bb80bf4b230ab1` reached SHIPPED in about 6 s (trace `0ef2068b9a3c2fdc81ab08a5fd921cf6`). No service is enrolled yet, so this is the pre-enrollment baseline for the mesh.
