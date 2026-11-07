# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 6/7. The control plane and Kiali are live (2026-11-06 22:18 EST). First enrollment approved; **[box1-workloads-dev#144](https://github.com/box1-org/box1-workloads-dev/pull/144) is open and waiting for the user's merge instruction.** The probe SNAT rule was dropped, because Postgres probes are `exec`.

## Done and verified
| Step | GitOps | Evidence |
|---|---|---|
| OVN local gateway mode | box1-gitops#93 `7acba8c` | `evidence/phase6-network-after.md` |
| OSSM 3.5.0 and Kiali 2.33.1 operators | box1-gitops#94 `9738e5b` | `evidence/phase6-operators.md` |
| Istio v1.31.1 ambient, CNI, ztunnel, metrics, Kiali | box1-gitops#95 `b71a407` | `evidence/phase6-control-plane-kiali.md` |

Measured cost so far: about 11m CPU and 1.2 GiB used; 440m and 1.4 GiB requested. The order flow is unchanged (about 6 s to SHIPPED).

## Known issues
- `gateways.networking.istio.io` stays with the ingress operator (install race). Ambient does not use it.
- The first sync of `service-mesh-control-plane` races istiod's webhook; it needs a re-sync. Fix: add an Argo retry or a health check.

## Next approval needed (box1-workloads-dev PR)
1. **Postgres NetworkPolicies** (six namespaces): add TCP 15008 from the service pod and ingress from `169.254.7.127/32` (ambient probe SNAT), beside 5432. Harmless before enrollment.
2. **Enroll `operations-console-dev`:** add `istio-discovery: enabled` and `istio.io/dataplane-mode: ambient` to `workloads/operations-console/namespace.yaml`. It has no database. Its pods are not restarted, because ambient captures traffic in place.

## Exact next action
After approval: open the workloads PR, wait for the user's merge instruction, and let Argo (auto-sync, selfHeal) apply it. Then:
- check the console's Route, its calls to order and inventory, and the order probe;
- check ztunnel logs and `istio_tcp_connections_opened_total{connection_security_policy="mutual_tls"}`;
- check that Kiali lists the namespace.

Then propose order and inventory, then the other four.
