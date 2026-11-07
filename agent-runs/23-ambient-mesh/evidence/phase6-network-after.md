# OVN local gateway mode: delivery and verification (2026-11-06 America/New_York)

**Change:** [box1-gitops#93](https://github.com/box1-org/box1-gitops/pull/93), squash-merged by the agent at the user's instruction as `7acba8c`. The Argo Application `service-mesh-network` was synced at 21:55:18 EST by setting its `operation` at that revision, with `ServerSideApply=true`. Result: `Succeeded`, `Synced`/`Healthy`. `networks.operator.openshift.io/cluster` now has `routingViaHost=true`.

**Rollout** (`phase6-network-rollout.log`):
- Both `ovnkube-control-plane` and `ovnkube-node` were replaced at 21:55:39.
- `ovnkube-node-flwp4` was 8/8 ready by 21:56:22, about 45 s after the sync.
- The `network` cluster operator was Progressing for one sample and never Degraded.
- The new `ovnkube-controller` runs with `--gateway-mode local --gateway-interface br-ex`.

**After the change (21:56–21:57 EST), compared with `phase6-network-before.txt`:**

| Check | Before | After |
|---|---|---|
| network / ingress / dns / kube-apiserver cluster operators | Available | Available, not Degraded |
| Running pods not ready | 0 | 0 |
| VMIs `legacy-erp`, `vm-golden-check` | Running | Running (no restart) |
| Console and order-service Routes `/q/health/ready` | 200 | 200 |
| Order through the ERP VM (SFTP) | `ord_dae76559…` SHIPPED about 6 s | `ord_b9097fb8…` SHIPPED about 8 s (trace `f5b35819805b7b77aa2faef8420009cb`) |
| `istiod-openshift-gateway`, GatewayClass `data-science-gateway-class` | 1/1, Accepted | 1/1, Accepted |
| Argo Applications not Synced/Healthy | — | none |
| Pod egress to `registry.redhat.io` (console and order pods) | not measured | HTTP response in about 0.1 s |

**Not measured:** how long traffic was interrupted during the rollout (no continuous probe ran), and RHOAI workloads beyond their Argo health.

**Rollback (not exercised):** delete the `service-mesh-network` Application, then set `routingViaHost: false`, which rolls `ovnkube-node` again.
