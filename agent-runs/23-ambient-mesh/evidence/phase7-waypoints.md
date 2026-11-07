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

## Step C: L7 on (box1-workloads-dev#152)
[box1-workloads-dev#152](https://github.com/box1-org/box1-workloads-dev/pull/152) was squash-merged at the user's instruction as `d4acbcf` (23:05:21 EST). The three namespaces carry `istio.io/use-waypoint: waypoint` from 23:05:31.

**Routing:** for console → order (6 connections) and console → inventory (5), the ztunnel outbound log shows `dst.workload="waypoint-…"` on 15008, so traffic goes through each namespace's waypoint.

**Traced order through the waypoint:**
- From the console pod, `POST order-service:8080/api/v1/orders` with `traceparent 00-8c795e7a6148dde512f01f7036c684a0-…-01` → **201**.
- `ord_dd7866b9cd5a45e6ae5c3f52939b28c8` kept trace ID `8c795e7a…` and reached SHIPPED in about 9 s.
- 5 × console → inventory GET and 5 × console → order GET → 200.

**L7 metrics** (`istio_requests_total`, `reporter="waypoint"`, `connection_security_policy="mutual_tls"`):
- order waypoint: `operations-console → order-service` 200 × 5, 201 × 1;
- inventory waypoint: `operations-console → inventory-service` 200 × 5.
- The labels include `source_principal=spiffe://cluster.local/ns/operations-console-dev/sa/operations-console` and the destination principal.

**Kiali** (versioned-app graph, 30 m, waypoints shown):
- **HTTP** edges `operations-console → order-service` and `→ inventory-service`, 100% mTLS. The rates read near-idle at this volume.
- TCP edges service → Postgres (100% mTLS), and to/from `unknown`.
- Kiali logs `WRN Multiple workloads found for GatewayAPI waypoint` for each namespace (cosmetic; not investigated).

**Defect: no waypoint spans in Tempo.**
- Trace `8c795e7a…` has 22 spans (order 3, inventory 11, notification 7, adapter 1), all from the applications.
- istiod: `Not able to configure requested tracing provider "box1-otel": … could not find service box1-collector.box1-observability.svc.cluster.local in Istio service registry`. The order waypoint's `config_dump` has no tracing block.
- **Cause:** the discovery selector excludes `box1-observability`.
- **Fix:** [box1-gitops#98](https://github.com/box1-org/box1-gitops/pull/98) labels that namespace `istio-discovery: enabled`, for discovery only.

## Interim L4 vs L7 vs trace (before the tracing fix)

| View | Shows | Misses |
|---|---|---|
| **L4 (ztunnel, Kiali TCP)** | every connection between workloads, mTLS on/off, bytes; service → Postgres; traffic to and from systems outside the mesh as `unknown` | requests, status codes, latency, anything per order |
| **L7 (waypoints, Kiali HTTP)** | requests per edge with response codes, latency histograms and caller identity (SPIFFE principal), for console → order and console → inventory only | Kafka (most of the order flow), Postgres (opted out), Route and Prometheus traffic (from outside the mesh, no waypoint) |
| **Tempo trace** | one order end to end through REST and Kafka: 4 services, 22 spans, causal order | transport security; whether a hop crossed the mesh |
