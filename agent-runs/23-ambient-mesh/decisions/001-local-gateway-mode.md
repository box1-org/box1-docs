# 001 OVN local gateway mode (`routingViaHost: true`) — proposed, needs approval

**Status:** proposed. **Blocks** every later step of this run.

**Finding:** ambient workloads' kubelet probes need OVN-Kubernetes local gateway mode. Three sources say so: Red Hat's OSSM 3.2 release notes, the OSSM 3.3 install prerequisites, and the OSSM ambient CI, which sets it before testing. This cluster has `routingViaHost: false` (see `evidence/phase0-discovery.md`).

**Proposal:** set `spec.defaultNetwork.ovnKubernetesConfig.gatewayConfig.routingViaHost: true` on `networks.operator.openshift.io/cluster`.
- Deliver it as a GitOps PR in `box1-gitops`, under `platform/service-mesh/network/`.
- The PR holds only that partial object, applied by a manual-sync Argo Application with `ServerSideApply=true`. Argo then owns only that one field.

**Impact (single node):**
- The Cluster Network Operator rolls `ovnkube-node`, which can briefly interrupt pod, VM and ingress traffic **cluster-wide**.
- Egress then follows the host routing table instead of OVN's gateway router. This affects every workload, not only the mesh.
- The effect on KubeVirt VMs (the ERP appliance), RHOAI and egress is **not tested**.
- Apply it in a quiet window, and check the order flow, the ERP SFTP path, Routes and the console afterwards.

**Rollback:** set the field back to `false`, which is another `ovnkube-node` rollout. Remove the Argo Application first, so it does not re-apply the setting.

**Alternatives considered:**
- Ambient without local gateway mode: probes fail by vendor statement, so this is rejected.
- Sidecar mode: excluded by the user decisions on #23.
