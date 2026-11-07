# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 1 Design, **stopped for approval** (2026-11-06 21:35 EST). Nothing has changed on the cluster. No GitOps branch or PR exists yet.

## Done
- Phase 0 discovery: `evidence/phase0-discovery.md`.
- Proposed decisions 001–005 in `decisions/`.

## Blocking finding
Ambient on OpenShift needs OVN **local gateway mode** (`routingViaHost: true`). The cluster has `false`. Changing it is a cluster-wide network change on the single node (decision 001).

## Open risk
The OSSM operator and the ingress operator both claim the `*.istio.io` CRDs. Whether they can share them is not established (decision 002). It is checked through a manually approved InstallPlan.

## Resource budget (requests, proposed)
| Component | CPU | Memory |
|---|---|---|
| istiod (`istio-system`) | 100m | 512Mi |
| Istio CNI DaemonSet | 100m | 100Mi |
| ztunnel DaemonSet | 200m | 512Mi |
| Kiali + operators (OSSM, Kiali) | 150m | 640Mi |
| 3 waypoints | 150m | 384Mi |
| **Total** | **about 0.7 core** | **about 2.1 GiB** |

Baseline: the node at 19% CPU and 63% memory (about 79 GiB of 125 GiB). This fits; it is measured in Phase 7.

## Approvals requested (all delivered as GitOps PRs)
1. The local gateway mode change (decision 001), with a short cluster-wide network blip.
2. Installing `servicemeshoperator3` `stable-3.5` and `kiali-ossm` `stable`, with manual InstallPlans (decision 002).
3. Kiali permissions: `cluster-monitoring-view` and `box1-traces-read-dev` (decision 003).

Later approvals, asked when reached: the mesh CRs (privileged DaemonSets), each namespace enrollment, the waypoints, and any default-deny.

## Exact next action
After approval 1:
- Open a `box1-gitops` PR with `platform/service-mesh/network/` and its manual-sync Application.
- After the user merges and syncs it, verify `routingViaHost`, OVN rollout completion, the order flow, ERP SFTP and Routes.

Then open the operators PR (approval 2) and inspect the InstallPlan's CRD steps before approving it.
