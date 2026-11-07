# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 7 live enrollment. **`operations-console-dev` is enrolled** (box1-workloads-dev#144 `ef49e76`, 22:24 EST). The Kiali namespace fix is live (box1-gitops#96 `0009516`); Kiali lists the nine namespaces and graphs the console. **Stopped for approval of the next enrollment.**

## Done and verified
| Step | GitOps | Evidence |
|---|---|---|
| OVN local gateway mode | box1-gitops#93 `7acba8c` | `evidence/phase6-network-after.md` |
| OSSM 3.5.0 / Kiali 2.33.1 operators | box1-gitops#94 `9738e5b` | `evidence/phase6-operators.md` |
| Istio v1.31.1 ambient, CNI, ztunnel, metrics, Kiali | box1-gitops#95 `b71a407` | `evidence/phase6-control-plane-kiali.md` |
| Postgres 15008 rules; console enrolled | box1-workloads-dev#144 `ef49e76` | `evidence/phase7-enroll-operations-console.md` |
| Kiali explicit namespaces; control-plane sync retry | box1-gitops#96 `0009516` | same file |

## Open
- `gateways.networking.istio.io` stays with the ingress operator (install race; unused).

## Exact next action
1. Done: #96 synced; Kiali shows nine namespaces.
2. Ask for approval to enroll `order-service-dev` and `inventory-service-dev` together. This is the first mTLS edge (order -> inventory) and covers Postgres under ambient.
3. After that: the Kiali TCP graph for a real order and the mTLS metric. Then the other four namespaces, the rollback exercise on one namespace, waypoints, and the NetworkPolicy baseline.
