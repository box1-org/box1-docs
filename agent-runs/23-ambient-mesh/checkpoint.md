# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 7 live enrollment. **`operations-console-dev` is enrolled** (box1-workloads-dev#144 `ef49e76`, 22:24 EST). The Kiali namespace fix is live (box1-gitops#96 `0009516`); Kiali lists the nine namespaces and graphs the console. **Console, order and inventory are enrolled** (#148 `5b596ce`, 22:39). mTLS is verified on console → order/inventory and service → Postgres. **All seven namespaces are enrolled** (#149 `cb603b2`, 22:44). mTLS is on every enrolled-to-enrolled edge, and the order flow through the ERP VM is verified. Rollback test approved; **box1-workloads-dev#150 (remove the console's mesh labels) is open and waiting for the user's merge instruction.** The in-mesh baseline was recorded at 22:47: 6/6 calls 200 with the console SPIFFE identity. After it merges, run `console-state.sh`-style checks, then open the restore PR, which re-adds both labels.

## Done and verified
| Step | GitOps | Evidence |
|---|---|---|
| OVN local gateway mode | box1-gitops#93 `7acba8c` | `evidence/phase6-network-after.md` |
| OSSM 3.5.0 / Kiali 2.33.1 operators | box1-gitops#94 `9738e5b` | `evidence/phase6-operators.md` |
| Istio v1.31.1 ambient, CNI, ztunnel, metrics, Kiali | box1-gitops#95 `b71a407` | `evidence/phase6-control-plane-kiali.md` |
| Postgres 15008 rules; console enrolled | box1-workloads-dev#144 `ef49e76` | `evidence/phase7-enroll-operations-console.md` |
| Kiali explicit namespaces; control-plane sync retry | box1-gitops#96 `0009516` | same file |
| order + inventory enrolled; mTLS proven; L4 vs trace | box1-workloads-dev#148 `5b596ce` | `evidence/phase7-enroll-order-inventory.md` |
| adapter, notification, asset, scenario-controller enrolled | box1-workloads-dev#149 `cb603b2` | `evidence/phase7-enroll-remaining.md` |

## Open
- `gateways.networking.istio.io` stays with the ingress operator (install race; unused).

## Status 2026-11-06 23:10 EST
- The rollback test PR box1-workloads-dev#150 is open; the user deferred it ("Not now").
- **Waypoints are drafted and need the user's approval and merges, in order:**
  1. [box1-gitops#97](https://github.com/box1-org/box1-gitops/pull/97): Argo RBAC for `gateways.gateway.networking.k8s.io` in the three namespaces. **Done:** merged as `fc4621a` and synced; Argo can now create Gateways in the three namespaces only.
  2. [box1-workloads-dev#151](https://github.com/box1-org/box1-workloads-dev/pull/151): a waypoint Gateway, a Telemetry (box1-otel, 100%) and a PodMonitor per namespace, plus `use-waypoint: none` on the order and inventory Postgres Services. **Inactive:** no traffic moves. Verify `Programmed`, pods ready, metrics `up`.
  3. PR C (not yet opened): `istio.io/use-waypoint: waypoint` on the three Namespaces. Then generate console → order/inventory calls carrying a `traceparent`, and compare the Kiali L4 graph, the L7 graph and the Tempo trace.
- **Prerequisites checked:**
  - the waypoint template is non-root, no privilege escalation, all capabilities dropped, and gets seccomp from `restricted-v2` (as the Postgres pods do);
  - service ports are named `http`;
  - Argo can create Telemetry and PodMonitors there but not Gateways (hence #97).
- **Expected L7 scope:** only mesh-sourced HTTP to the waypointed services, that is console → order and console → inventory (and console → console via its own waypoint, if any). Router (Route) and Prometheus traffic come from outside the mesh and bypass waypoints unless `istio.io/ingress-use-waypoint` is set.

## Exact next action
- **L7 is on** (#152 `d4acbcf`): HTTP metrics and Kiali HTTP edges are verified (`evidence/phase7-waypoints.md`).
- **Waypoint tracing is broken:** istiod cannot resolve `box1-collector` because `box1-observability` is outside the discovery selectors. The fix is [box1-gitops#98](https://github.com/box1-org/box1-gitops/pull/98), waiting for the user's merge instruction. After it merges:
  1. sync `observability-tracing`;
  2. confirm the istiod warning is gone and the waypoint `config_dump` has a tracing block;
  3. send a new console-pod request with a `traceparent` and confirm the waypoint spans appear in Tempo;
  4. finish the L4/L7/trace comparison and the waypoint recommendation for the other four namespaces.
- The rollback test #150 now conflicts with #152 (same `namespace.yaml`); rebase it when the user resumes it.
