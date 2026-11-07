# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 6 GitOps delivery of the prerequisites. **Local gateway mode is live and verified** (2026-11-06 21:57 EST; `evidence/phase6-network-after.md`). The operators PR #94 waits on the user; they chose to merge only #93 for now.

## Approvals (user, chat, 2026-11-06)
- Decision 001: local gateway mode.
- Decision 002: OSSM `stable-3.5` and Kiali operators.
- Decision 003: Kiali permissions (`cluster-monitoring-view` and `box1-traces-read-dev`).

Merging is not part of those approvals. The agent's merge attempt was refused by the session's permission policy, so the user merges.

## Open PRs
- [box1-gitops#93](https://github.com/box1-org/box1-gitops/pull/93): the `service-mesh-network` Application. It sets `routingViaHost: true` by server-side apply. CI passed.
- [box1-gitops#94](https://github.com/box1-org/box1-gitops/pull/94): the `service-mesh-operators` Application, with Subscriptions in their own namespaces and Manual InstallPlans.

## Baseline before the network change
See `evidence/phase6-network-before.txt` (21:51 EST):
- `ovnkube-node` age 15d;
- the network and ingress cluster operators were Available;
- 0 Running pods were not ready;
- both VMIs were Running;
- the console and order-service Routes returned 200;
- order `ord_dae76559f66643f7b9b07ed59e425c31` reached SHIPPED in about 6 s (trace `a10ee959ee104b5d33bc6fe571b871d3`).

## Exact next action
1. Done: after #93 merged (`7acba8c`), sync `service-mesh-network` by setting the Application `operation` at the merge revision.
2. Watch the `ovnkube-node` rollout and the `network` cluster operator.
3. Repeat the baseline checks and an order probe. Record the results in `evidence/phase6-network-after.md`.
4. After #94 merges, about 10 s after #93: sync `service-mesh-operators`.
5. Inspect both InstallPlans, especially the OSSM CRD steps against the ingress-owned `*.istio.io` CRDs.
6. Approve the InstallPlans, then verify that `istiod-openshift-gateway` and the GatewayClasses stay healthy.
7. Then stop for approval of the mesh CRs (`Istio`, `IstioCNI`, `ZTunnel`) and the Kiali CR with its permissions.

Kiali's permissions (decision 003) are delivered with the Kiali CR, not with the operators.
