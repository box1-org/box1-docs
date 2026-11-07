# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 7 live enrollment. **`operations-console-dev` is enrolled** (box1-workloads-dev#144 `ef49e76`, 22:24 EST). The Kiali namespace fix is live (box1-gitops#96 `0009516`); Kiali lists the nine namespaces and graphs the console. **Console, order and inventory are enrolled** (#148 `5b596ce`, 22:39). mTLS is verified on console → order/inventory and service → Postgres. The remaining four are approved; **box1-workloads-dev#149 is open and waiting for the user's merge instruction.**

## Done and verified
| Step | GitOps | Evidence |
|---|---|---|
| OVN local gateway mode | box1-gitops#93 `7acba8c` | `evidence/phase6-network-after.md` |
| OSSM 3.5.0 / Kiali 2.33.1 operators | box1-gitops#94 `9738e5b` | `evidence/phase6-operators.md` |
| Istio v1.31.1 ambient, CNI, ztunnel, metrics, Kiali | box1-gitops#95 `b71a407` | `evidence/phase6-control-plane-kiali.md` |
| Postgres 15008 rules; console enrolled | box1-workloads-dev#144 `ef49e76` | `evidence/phase7-enroll-operations-console.md` |
| Kiali explicit namespaces; control-plane sync retry | box1-gitops#96 `0009516` | same file |
| order + inventory enrolled; mTLS proven; L4 vs trace | box1-workloads-dev#148 `5b596ce` | `evidence/phase7-enroll-order-inventory.md` |

## Open
- `gateways.networking.istio.io` stays with the ingress operator (install race; unused).

## Exact next action
1. Done: #96 synced; Kiali shows nine namespaces.
2. Done: order and inventory enrolled; mTLS proven.
3. Next, after approval: enroll fulfillment-adapter, notification, asset and scenario-controller in one PR. Each has a database, so expect the same ~2 s pooled-connection reset. Check the adapter → ERP VM SFTP path (VM outside the mesh) with an order probe.
4. Then: the rollback exercise on one namespace, waypoints on console, order and inventory, and the NetworkPolicy baseline.
