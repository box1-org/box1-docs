# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 7 live enrollment. **`operations-console-dev` is enrolled** (box1-workloads-dev#144 `ef49e76`, 22:24 EST). Waiting for the user's merge instruction on **box1-gitops#96** (the Kiali namespace fix).

## Done and verified
| Step | GitOps | Evidence |
|---|---|---|
| OVN local gateway mode | box1-gitops#93 `7acba8c` | `evidence/phase6-network-after.md` |
| OSSM 3.5.0 / Kiali 2.33.1 operators | box1-gitops#94 `9738e5b` | `evidence/phase6-operators.md` |
| Istio v1.31.1 ambient, CNI, ztunnel, metrics, Kiali | box1-gitops#95 `b71a407` | `evidence/phase6-control-plane-kiali.md` |
| Postgres 15008 rules; console enrolled | box1-workloads-dev#144 `ef49e76` | `evidence/phase7-enroll-operations-console.md` |

## Open
- **box1-gitops#96:** Kiali lists the namespaces explicitly, because the operator does not watch labels; plus a sync retry on `service-mesh-control-plane`.
- `gateways.networking.istio.io` stays with the ingress operator (install race; unused).

## Exact next action
1. After #96 merges: refresh `box1-root`, then sync `service-mesh-kiali` at the merge revision. Confirm `/api/namespaces` lists the nine namespaces and Kiali shows console traffic.
2. Ask for approval to enroll `order-service-dev` and `inventory-service-dev` together. This is the first mTLS edge (order -> inventory) and covers Postgres under ambient.
3. After that: the Kiali TCP graph for a real order and the mTLS metric. Then the other four namespaces, the rollback exercise on one namespace, waypoints, and the NetworkPolicy baseline.
