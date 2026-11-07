# Enrollment 1: operations-console-dev (2026-11-06 America/New_York)

**Change:** [box1-workloads-dev#144](https://github.com/box1-org/box1-workloads-dev/pull/144), squash-merged at the user's instruction as `ef49e76` (22:24:16 EST).
- Argo auto-sync applied it to all seven Applications within about 20 s; all are `Synced`/`Healthy` at `ef49e76`.
- The six `<service>-postgres` NetworkPolicies now allow 5432 and 15008.
- `operations-console-dev` carries `istio-discovery: enabled` and `istio.io/dataplane-mode: ambient`.

## Observed
- **Capture without restart:** pod `operations-console-55c87cb654-sgzl9` has `ambient.istio.io/redirection: enabled`, restart count 0, and is ready. Ztunnel logged `inpod::statemanager pod received, starting proxy` at 03:24:31Z.
- **Probes keep working under ambient with local gateway mode:** the pod stayed ready, and the console Route `/q/health/ready` returns 200; `/` returns 302 (login).
- **Outbound through ztunnel, from inside the console pod:**
  - `order-service:8080/api/v1/orders` → 200;
  - `inventory-service:8080/api/v1/inventory` → 200;
  - `box1-collector:4318` → reachable (404 on `/`).
  - The ztunnel access log shows the outbound connections for `src.workload=operations-console-…` with no destination identity, because the peers are not in the mesh yet.
- **Metrics:** `istio_tcp_connections_opened_total{source_workload_namespace="operations-console-dev"}` = 7 in Thanos, `connection_security_policy="unknown"`, `reporter="source"`. That is expected: **no mTLS until a peer namespace is enrolled.**
- **Console logs:** no WARN or ERROR in the 3 minutes after enrollment.
- **Business flow:** order `ord_996c049f319840668aeed814e773ec04` reached SHIPPED in about 7 s (trace `ecaacf60ea1f8725a0fb499753f26586`). It went through the order API Route, not the console UI.

## Defect found: Kiali does not see the namespace
- `/api/namespaces` still returns only `istio-system` and `ztunnel`.
- Kiali CR status: `discoverySelectorNamespaces: istio-system,ztunnel` (last reconcile 03:17Z). There is no Kiali RoleBinding in `operations-console-dev`.
- **Cause:** the Kiali operator evaluates `discovery_selectors` only when it reconciles, and does not watch namespace labels.
- **Fix:** [box1-gitops#96](https://github.com/box1-org/box1-gitops/pull/96) names the nine namespaces explicitly (`kubernetes.io/metadata.name In [...]`), which triggers a reconcile and covers the later enrollments. It also adds an Argo sync retry to `service-mesh-control-plane`.

## Not tested
- A signed-in console session in a browser.
- The console's Keycloak token calls after enrollment.

## Fix delivered: Kiali namespaces (22:28–22:30 EST)
- [box1-gitops#96](https://github.com/box1-org/box1-gitops/pull/96) was squash-merged at the user's instruction as `0009516`. `service-mesh-kiali` was synced at that revision (`Succeeded`/`Synced`).
- `service-mesh-control-plane` now carries `syncPolicy.retry` (limit 5, 20 s backoff, max 3 m) and is `Synced`.
- The Kiali operator reconciled at 22:29. Its status `discoverySelectorNamespaces` now lists the nine namespaces, and `kiali-viewer` RoleBinding `kiali` exists in `operations-console-dev`.
- The Kiali pod was replaced during the reconcile. One `/api/namespaces` call during the rollover returned an empty body.
- `/api/namespaces` then returned the nine namespaces: `istio-system`, `ztunnel` and the seven service namespaces.
- **Kiali workload graph** for `operations-console-dev` (10 m):
  - node `operations-console`;
  - TCP edges `unknown → operations-console` (7.02) and `operations-console → unknown` (77.68);
  - `isMTLS` unset.
  - `unknown` is expected while the peers (order, inventory, the router) are outside the mesh.
