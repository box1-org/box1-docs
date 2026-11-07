# Waypoints (L7) — delivery log (2026-11-06 America/New_York)

## Step A: Argo CD may manage waypoint Gateways
- [box1-gitops#97](https://github.com/box1-org/box1-gitops/pull/97), squash-merged at the user's instruction as `fc4621a` (22:59:23 EST).
- `service-mesh-control-plane` was synced at that revision: `Succeeded`, `Synced`/`Healthy`.
- `oc auth can-i create gateways.gateway.networking.k8s.io --as=<argocd controller>`:
  - yes in `operations-console-dev`, `order-service-dev` and `inventory-service-dev`;
  - still **no** in `asset-service-dev`, so the scope is correct.
