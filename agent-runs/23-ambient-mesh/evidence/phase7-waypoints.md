# Waypoints (L7) — delivery log (2026-11-06 America/New_York)

## Step A: Argo CD may manage waypoint Gateways
- [box1-gitops#97](https://github.com/box1-org/box1-gitops/pull/97), squash-merged at the user's instruction as `fc4621a` (22:59:23 EST).
- `service-mesh-control-plane` was synced at that revision: `Succeeded`, `Synced`/`Healthy`.
- `oc auth can-i create gateways.gateway.networking.k8s.io --as=<argocd controller>`:
  - yes in `operations-console-dev`, `order-service-dev` and `inventory-service-dev`;
  - still **no** in `asset-service-dev`, so the scope is correct.

## Step B: waypoints deployed, not in use
- [box1-workloads-dev#151](https://github.com/box1-org/box1-workloads-dev/pull/151), squash-merged at the user's instruction as `599b241` (23:02:16 EST). Auto-synced: `operations-console`, `order-service` and `inventory-service` are `Synced`/`Healthy`.
- In each namespace:
  - `Gateway/waypoint` is `Accepted=True Programmed=True ResolvedRefs=True`;
  - `Deployment/waypoint` is 1/1;
  - the pod runs under SCC `restricted-v2` with seccomp `RuntimeDefault` (Pod Security `restricted` admitted it) and requests 100m / 128Mi.
- Service addresses: console `172.30.11.193`, order `172.30.208.237`, inventory `172.30.117.192`.
- `up{pod=~"waypoint-.*"}` = 1 for all three (PodMonitor 15020).
- `istio_requests_total` from the waypoints is empty, as expected while no namespace has `use-waypoint`.
- `order-service-postgres` and `inventory-service-postgres` carry `istio.io/use-waypoint: none`.
- `istiod-openshift-gateway` is untouched.
- Order `ord_9b3c9e74c9c34c5b958345071f872401` reached SHIPPED in about 9 s.

## Step C: opened
[box1-workloads-dev#152](https://github.com/box1-org/box1-workloads-dev/pull/152) adds `istio.io/use-waypoint: waypoint` to the three namespaces. It passed the server dry run. It touches `workloads/operations-console/namespace.yaml`, as the deferred rollback PR #150 does, so whichever merges second needs a rebase.
