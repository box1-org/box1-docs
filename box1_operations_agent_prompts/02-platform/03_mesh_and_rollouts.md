# Platform 03 — Ambient service mesh and Kiali observability


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** PLT-04/05; NFR-01/05; DEMO-A3 (mesh visibility only; the rollout part is removed, see below)

**Dependencies:** Working Core services, Platform 02 observability (Tempo, the OpenTelemetry collector and user-workload monitoring), and verified OpenShift Service Mesh 3 and Kiali versions and CRDs.

## Mission

Prove identity-aware communication and make it visible: ambient-mode mTLS between the Box1 services, seen in Kiali and lined up with the existing Tempo traces. This is not a decorative Istio dashboard. Start at L4 with ztunnel only, and add L7 waypoints only where the extra visibility is worth their cost on the single node.

## Implementation scope and guardrails

- Detect the OpenShift release, the available OpenShift Service Mesh 3 and Kiali operator versions, whether ambient mode is supported for that version, and the OVN-Kubernetes settings ambient needs. Record a CPU/memory baseline before install, and avoid unsupported custom resources.
- **Coexist with the platform's Istio.** OpenShift's Gateway API already runs an `istiod` in `openshift-ingress` and owns the `*.istio.io` CRDs. The mesh control plane must not reconcile that gateway's resources or break ingress. Use a distinct revision and discovery selectors, as the chosen OSSM version documents.
- Install OSSM 3 in the **ambient** profile (`Istio`, `IstioCNI`, `ZTunnel`) and **Kiali** through GitOps. Kiali uses OpenShift login and sees only the control-plane, ztunnel and enrolled service namespaces (no cluster-wide access). It reads metrics from user-workload monitoring through Thanos Querier, and links to Tempo through its existing gateway.
- Enroll the seven Box1 service namespaces (`order-service`, `inventory-service`, `fulfillment-adapter`, `notification-service`, `asset-service`, `scenario-controller`, `operations-console`, each `-dev`) in **ambient L4** with no waypoints. Do one namespace first, then the rest. Removing the namespace label is the rollback. Do not enroll the ERP VM, Kafka, Keycloak or platform namespaces.
- With a real order flow, inspect the Kiali TCP graph and prove mTLS is negotiated, using ztunnel metrics or logs (`connection_security_policy="mutual_tls"`) and Kiali. Probes, metrics scraping, Kafka, Postgres, Keycloak, the collector and the ERP SFTP path must keep working.
- Add **waypoints** to `operations-console-dev`, `order-service-dev` and `inventory-service-dev`. For the **same `orderId`**, compare the L4 graph, the L7 graph and the Tempo trace. Decide whether waypoints should send spans to the existing collector. Recommend whether the extra L7 visibility justifies waypoints for the other four namespaces; that decision is the user's.
- Baseline NetworkPolicy on the sensitive DB, Kafka and ERP paths. It must work under ambient, for example by allowing HBONE port 15008. Add any deny-all one step at a time, and verify that platform webhooks, DNS and monitoring still work.
- Measure the resource cost of istiod, the CNI, ztunnel, Kiali and each waypoint against the baseline. State explicitly that one node cannot deliver failure-domain HA.

**Removed by user decision (2026-11-06, [#23](https://github.com/box1-org/box1-docs/issues/23)):** canary releases (traffic splitting, revision routing, abort and rollback), the AuthorizationPolicy deny test, mesh retry and timeout ownership, and the ERP reset/replay criterion. The earlier "one business path first" rule is replaced by L4 enrollment of all seven namespaces.

## Verifiable acceptance evidence

- The order flow works before enrollment, under ambient L4 on all seven namespaces, and after one namespace is rolled back. mTLS is actually negotiated and measurable.
- Kiali is GitOps-managed and rejects anonymous access. Its TCP graph shows a real order's flow across the seven namespaces.
- Waypoints on the three namespaces produce an L7 graph. The L4 graph, L7 graph and Tempo trace for one `orderId` are recorded side by side, with a waypoint recommendation for the other namespaces.
- The NetworkPolicy baseline works under ambient: allowed flows pass, a blocked flow is refused, and DNS and monitoring are unaffected.
- The resource cost of the mesh, Kiali and the waypoints is measured on the single node, and the ingress Gateway API is unaffected.

## Nominal 64K-context implementation slices

1. Compatibility, capacity and coexistence inventory; pin the OSSM and Kiali versions.
2. OSSM ambient and Kiali; L4 enrollment of one namespace, then all seven; mTLS proof.
3. Waypoints on the three namespaces, the Tempo link, and the L4/L7/trace comparison.
4. NetworkPolicy baseline, resource cost and the waypoint recommendation.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
