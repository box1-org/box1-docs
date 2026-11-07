# Checkpoint — #23 ambient mesh and Kiali

**Phase:** 6, prerequisites delivered; mesh and Kiali approved (user, 2026-11-06); **[box1-gitops#95](https://github.com/box1-org/box1-gitops/pull/95) open, waiting for the user's merge instruction** (22:20 EST).

## Done and verified
- OVN local gateway mode: box1-gitops#93 `7acba8c`. See `evidence/phase6-network-after.md`.
- OSSM 3.5.0 and Kiali 2.33.1 operators: box1-gitops#94 `9738e5b`. See `evidence/phase6-operators.md`.
  - 14 of the 15 `*.istio.io` CRDs are now OLM-managed.
  - `gateways.networking.istio.io` stayed with the ingress operator (race at install; unused by ambient).
  - No ownership flapping; the ingress istiod and the GatewayClass are healthy.

## Approvals
- User, chat, 2026-11-06: decisions 001, 002 and 003.
- Merges of #93 and #94: separate user instructions.

## Next approval needed
GitOps PRs for:
1. The mesh, as `platform/service-mesh/mesh/` in box1-gitops:
   - Namespaces `istio-system`, `istio-cni` and `ztunnel`, labelled `istio-discovery=enabled` before the ZTunnel;
   - `Istio` `default`: `profile: ambient`, `version: v1.31.1`, `trustedZtunnelNamespace: ztunnel`, discoverySelectors `istio-discovery: enabled`, and the `box1-otel` extensionProvider pointing at `box1-collector.box1-observability:4317`;
   - `IstioCNI` and `ZTunnel`, which are privileged DaemonSets;
   - the Telemetry for the prometheus provider, and PodMonitors for ztunnel;
   - Argo RBAC for the `sailoperator.io` cluster-scoped kinds.
2. Kiali, as `platform/service-mesh/kiali/`: the `Kiali` CR with `cluster_wide_access=false`, Thanos and Tempo wiring, and the `cluster-monitoring-view` and `box1-traces-read-dev` bindings (already approved).
3. Workloads, in box1-workloads-dev: allow 15008 and the probe SNAT address on the `<service>-postgres` NetworkPolicies, then the ambient label on `operations-console-dev` first.

## Exact next action
PR 1 and PR 2 are combined in #95, which passed the server-side dry run. After the user says to merge, sync in this order:
1. `service-mesh-control-plane`, then wait for `Istio` Ready and the CNI and ztunnel DaemonSets to be ready;
2. `observability-tracing` (the NetworkPolicy);
3. `service-mesh-kiali`.

Then verify:
- the ingress istiod and GatewayClass are unaffected;
- ztunnel metrics reach Thanos;
- Kiali requires a login and lists only labelled namespaces;
- Kiali reaches Tempo;
- the resource cost against the baseline;
- the order probe still passes.

After that, ask for approval of the PR 3 workloads change (Postgres NetworkPolicies, then `operations-console-dev` enrollment).
