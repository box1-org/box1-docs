# Ambient service mesh and Kiali: mTLS on all seven Box1 services, L7 waypoints and Tempo-linked traces

**Date:** 2026-11-06 (America/New_York). Work ran from 21:30 to 23:20 EST.

**Status:** Delivered and live. Acceptance is partial: [box1-docs#23](https://github.com/box1-org/box1-docs/issues/23) stays open with 3 of 5 criteria ticked, each with cluster proof.
- **Open:** criterion 1 needs the one-namespace rollback test. Its PR is open, deferred by the user and now in conflict.
- **Not started:** criterion 4, the NetworkPolicy baseline.

This was a `frontier` profile run. Its run state, decisions 001–006 and evidence are on branch [`agent-run/23-ambient-mesh`](https://github.com/box1-org/box1-docs/tree/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh). That branch is not merged.

## Outcome

**mTLS:** all seven Box1 service namespaces run in **Istio ambient mode**, from Red Hat OpenShift Service Mesh 3.5. Every connection between two enrolled workloads is mutual TLS with SPIFFE workload identities, and no application pod was restarted. The order flow, including the SFTP hop to the ERP VM outside the mesh, still works.

**Kiali** is GitOps-managed, requires an OpenShift login and is limited to the mesh and Box1 namespaces. It draws the TCP graph, and the HTTP graph where waypoints exist.

**Waypoints (L7)** run in `operations-console-dev`, `order-service-dev` and `inventory-service-dev`. They add per-request HTTP metrics: response code, latency, and caller and callee identity. They also add a span to the caller's trace, so in Tempo a waypoint hop appears as the parent of the service's own server span.

**Scope, by user decision on #23** ([plan comment](https://github.com/box1-org/box1-docs/issues/23#issuecomment-6698809998)):
- no canary releases;
- no AuthorizationPolicy deny test;
- no mesh retry or timeout policy;
- no ERP reset criterion.

The prompt was rewritten to match in [box1-docs#93](https://github.com/box1-org/box1-docs/pull/93).

| Item | Value |
|---|---|
| Operators (OLM, manual InstallPlans, GitOps-managed) | `servicemeshoperator3.v3.5.0` (channel `stable-3.5`) in `openshift-service-mesh-operator`; `kiali-operator.v2.33.1` (channel `stable`) in `openshift-kiali-operator` |
| Control plane | `Istio/default`, ambient profile, `v1.31.1`, revision `default`, in `istio-system`. Discovery selector `istio-discovery: enabled`. Extension provider `box1-otel` → `box1-collector.box1-observability:4317` |
| Data plane | `IstioCNI/default` (`istio-cni`) and `ZTunnel/default` (`ztunnel`), both privileged DaemonSets |
| Enrolled | `operations-console-dev`, `order-service-dev`, `inventory-service-dev`, `fulfillment-adapter-dev`, `notification-service-dev`, `asset-service-dev`, `scenario-controller-dev`, labelled `istio.io/dataplane-mode: ambient` and `istio-discovery: enabled` |
| Waypoints | `Gateway/waypoint` (`istio-waypoint`, for services) plus `Telemetry/waypoint-tracing` (100%) and a PodMonitor, in console, order and inventory. Those namespaces carry `istio.io/use-waypoint: waypoint`. The order and inventory Postgres Services opt out with `istio.io/use-waypoint: none` |
| Kiali | `https://kiali-istio-system.apps.ocp.box1.org`. `auth.strategy: openshift`, `cluster_wide_access: false`, an explicit list of nine namespaces. Metrics from Thanos Querier; traces from the Tempo gateway (tenant `dev`) |
| Cluster network | OVN-Kubernetes **local gateway mode** (`routingViaHost: true`), required for ambient |
| GitOps | `box1-gitops`: Applications `service-mesh-network`, `service-mesh-operators`, `service-mesh-control-plane` and `service-mesh-kiali` (manual sync, `platform/service-mesh/`), plus the existing `observability-tracing`. `box1-workloads-dev`: namespace labels, waypoints and NetworkPolicies (auto-sync) |

## Starting baseline

Observed read-only on 2026-11-06 at about 21:00 EST ([phase0-discovery.md](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase0-discovery.md)):
- **Cluster:** OpenShift `5.0.0-rc.7`, single node `quark`, OVN-Kubernetes with `routingViaHost: false`. Load was 19% CPU and 63% memory.
- **No service mesh:** no OSSM, Sail, Kiali, ztunnel or CNI installed.
- **Istio was already present.** The ingress operator runs `istiod-openshift-gateway` (revision `openshift-gateway`, Istio 1.30.4) in `openshift-ingress` for the Gateway API, and owns the `*.istio.io` CRDs. Its CA lives in its own ConfigMap, `openshift-gw-ca-root-cert`.
- **Workloads:** the seven services each have one pod, and six have a Postgres pod. Each Postgres had a NetworkPolicy allowing only 5432 from its service.
- **Order flow:** order `ord_dae76559…` reached SHIPPED in about 6 s through the ERP VM.
- **Observability from [#22](2026-11-06-observability-tracing-metrics.md):** Tempo behind its gateway, the OTel collector, and user-workload monitoring scraping all seven services.

## What changed

| Step | PR | Merge | Change |
|---|---|---|---|
| Prompt | [box1-docs#93](https://github.com/box1-org/box1-docs/pull/93) | `2d0d078` | Mesh prompt rewritten for ambient + Kiali per the user's decisions |
| Network | [box1-gitops#93](https://github.com/box1-org/box1-gitops/pull/93) | `7acba8c` | `service-mesh-network`: server-side-apply partial `Network` setting `routingViaHost: true` |
| Operators | [box1-gitops#94](https://github.com/box1-org/box1-gitops/pull/94) | `9738e5b` | `service-mesh-operators`: OSSM 3.5 and Kiali subscriptions, manual InstallPlans, own namespaces |
| Control plane + Kiali | [box1-gitops#95](https://github.com/box1-org/box1-gitops/pull/95) | `b71a407` | `Istio`/`IstioCNI`/`ZTunnel`, Prometheus `Telemetry`, istiod ServiceMonitor, ztunnel PodMonitor, Argo RBAC; `Kiali` with `cluster-monitoring-view` and `box1-traces-read-dev` bindings; Tempo gateway NetworkPolicy admits Kiali |
| Fix | [box1-gitops#96](https://github.com/box1-org/box1-gitops/pull/96) | `0009516` | Kiali namespaces listed explicitly; `syncPolicy.retry` on `service-mesh-control-plane` |
| Enrollment 1 | [box1-workloads-dev#144](https://github.com/box1-org/box1-workloads-dev/pull/144) | `ef49e76` | Postgres NetworkPolicies also allow HBONE 15008; `operations-console-dev` enrolled |
| Enrollment 2 | [box1-workloads-dev#148](https://github.com/box1-org/box1-workloads-dev/pull/148) | `5b596ce` | `order-service-dev`, `inventory-service-dev` enrolled |
| Enrollment 3 | [box1-workloads-dev#149](https://github.com/box1-org/box1-workloads-dev/pull/149) | `cb603b2` | adapter, notification, asset, scenario-controller enrolled |
| Waypoint RBAC | [box1-gitops#97](https://github.com/box1-org/box1-gitops/pull/97) | `fc4621a` | Argo may manage Gateway API `Gateway`s in the three L7 namespaces only |
| Waypoints | [box1-workloads-dev#151](https://github.com/box1-org/box1-workloads-dev/pull/151) | `599b241` | Waypoint, tracing Telemetry, PodMonitor per namespace; Postgres opt-out; **inactive** |
| L7 on | [box1-workloads-dev#152](https://github.com/box1-org/box1-workloads-dev/pull/152) | `d4acbcf` | `istio.io/use-waypoint: waypoint` on the three namespaces |
| Fix | [box1-gitops#98](https://github.com/box1-org/box1-gitops/pull/98) | `68b16f4` | `box1-observability` labelled `istio-discovery: enabled` (discovery only) so istiod can resolve the collector for waypoint tracing |

The user approved each change in chat and instructed each merge. Two merges attempted on approval alone were refused by the session's permission policy, so merging was always done on an explicit instruction.

**Made outside Git, with the user's approval:**
- Argo syncs of the manual-sync Applications, each triggered by setting the Application `operation` at the merge revision.
- Approval of the two operator InstallPlans (`install-zf556`, `install-r22q8`), after their steps were inspected.

**Decisions with consequences** (records are in the run state's `decisions/`):
- **Local gateway mode (001).** Red Hat's OSSM release notes and install prerequisites say ambient probes need it, and the OSSM ambient CI sets it.
  - It is **cluster-wide**: the change restarted `ovnkube-node`, and egress now follows the host routing table for every workload.
  - It is GitOps-managed as a single field via server-side apply.
- **Coexistence with the Gateway API istiod (002):**
  - a separate revision (`default`) and a discovery selector that never includes `openshift-ingress`;
  - separate CA ConfigMaps;
  - operators in their own namespaces, not `openshift-operators`, where a Manual subscription would have held other operators' upgrades.
- **Kiali least privilege (003):** `cluster_wide_access: false`, with an explicit namespace list (see below).
- **Postgres in the mesh (004):** each service → Postgres connection is mTLS, so the NetworkPolicies allow 15008. The probe-SNAT rule was not needed, because Postgres probes are `exec`.
- **Waypoints in three steps (005):**
  1. RBAC;
  2. waypoints deployed but inactive, then verified;
  3. the label switch.

  Postgres opts out, so the DB path stays L4.
- **Waypoint scope (006):** recommended **not** to add waypoints to the other four namespaces. This is a recommendation; the user has not decided.

## Validation and evidence

| Test | Expected | Observed |
|---|---|---|
| Local gateway mode | Field set; cluster healthy | `routingViaHost=true`. `ovnkube-node` back 8/8 in about 45 s, `--gateway-mode local`. Network operator never Degraded. No unready pods; VMs not restarted; Routes 200; pod egress works. Order shipped in about 8 s ([evidence](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase6-network-after.md)) |
| Operator install vs ingress-owned CRDs | Gateway API istiod unaffected | 14 of 15 `*.istio.io` CRDs moved to OLM; `gateways.networking.istio.io` stayed ingress-owned (see Limitations). No ownership flapping over 2 min. `istiod-openshift-gateway` and `data-science-gateway-class` healthy ([evidence](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase6-operators.md)) |
| Control plane | Healthy; no namespace touched | `Istio`, `IstioCNI` and `ZTunnel` Healthy on `v1.31.1` within 30 s. `istio-ca-root-cert` only in the mesh namespaces. Ingress istiod not restarted ([evidence](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase6-control-plane-kiali.md)) |
| Kiali access | Login required; limited scope | Anonymous `/api/namespaces` → **401**. With a token: exactly the nine listed namespaces. istiod, Prometheus and Tempo status **Healthy** |
| Enrollment | No pod restarts; flow works | 13 pods captured in place (`ambient.istio.io/redirection: enabled`, 0 restarts). Orders shipped in 6–9 s after each step, including through the adapter → ERP VM SFTP path |
| **mTLS** | Negotiated and measurable | `istio_tcp_connections_opened_total{connection_security_policy="mutual_tls"}`, reported by both ends, on console → order, inventory, adapter and asset, and on each of the six service → Postgres edges. The ztunnel log shows SPIFFE identities (e.g. `ns/operations-console-dev/sa/operations-console` → `ns/order-service-dev/sa/order-service`). Kiali shows these edges at 100% mTLS. Postgres sees the service pod IP, so NetworkPolicies still match ([evidence](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase7-enroll-order-inventory.md)) |
| Waypoints | Deploy under `restricted` PSA; inert until labelled | All three `Programmed`, ready under SCC `restricted-v2` with RuntimeDefault seccomp, scraped; no requests until #152 |
| L7 metrics | Per-request data | `istio_requests_total{reporter="waypoint"}`: console → order 200 × 5 and 201 × 1; console → inventory 200 × 5; `mutual_tls` with both principals. Kiali shows HTTP edges |
| **Waypoint spans in Tempo** | Waypoint parents the service span | Trace `8670e0b4…` (`ord_2f6bb653…`, SHIPPED in about 7 s): `waypoint.order-service-dev` (4.82 ms) → `POST /api/v1/orders` (4.24 ms); `waypoint.inventory-service-dev` (2.08 ms) → `GET /api/v1/inventory` (1.45 ms); then the Kafka consumer spans ([evidence](https://github.com/box1-org/box1-docs/blob/agent-run/23-ambient-mesh/agent-runs/23-ambient-mesh/evidence/phase7-waypoints.md)) |

**L4 vs L7 vs trace, for the same order:**
- **L4 (ztunnel, Kiali TCP):** connections and their mTLS status. Kafka, Keycloak, the router and the ERP VM appear as `unknown`.
- **L7 (waypoints):** requests, status, latency and caller identity, but **only** for the console's HTTP calls. Kafka carries most of an order's path and is invisible at L7.
- **Tempo:** the order end to end across Kafka, now including the waypoint hops, but nothing about transport security.

**Resource cost** (point-in-time and 15-minute Prometheus samples; the node is 31.5 CPU and about 125 GiB):

| Component | CPU used | Memory used | Requested |
|---|---|---|---|
| istiod | 2m | 168 MiB | 100m / 512 MiB |
| istio-cni-node | 1m | 140 MiB | 100m / 100 MiB |
| ztunnel (seven namespaces enrolled) | 6m | 10 MiB | 200m / 512 MiB |
| Kiali | 3m | 76 MiB | 20m / 128 MiB |
| OSSM + Kiali operators | 4m | about 0.9 GiB | 20m / 128 MiB |
| 3 waypoints (15-min peak) | about 3m | about 98 MiB | 300m / 384 MiB |

- The waypoints reserve about 100× what they use.
- Each waypoint hop added about 0.6 ms in **one** sample. Waypoint traffic was near idle (about 1 request per 15 minutes per waypoint), so these numbers are a floor, not a load figure.
- The node's own memory moved by ±3 GiB between samples, which is more than the whole mesh.

**Not tested or not established:**
- **Rollback** of a namespace (criterion 1). See Follow-ups.
- **NetworkPolicy baseline** (criterion 4): egress allow-lists, a blocked-flow test and any default-deny.
- **Kiali login in a browser.** Access was proven through the API with an OpenShift token.
- **Traffic interruption length** during the OVN restart (no continuous probe ran), and the effect of local gateway mode on RHOAI workloads beyond their Argo health.
- **Whether synchronous API calls failed** during the 1–3 s database reset at enrollment.
- **Waypoint behaviour under load:** latency and CPU at real request rates.
- **Vendor support** for OSSM 3.5 and Kiali 2.33 on OpenShift 5.0.0-rc.7.

## Incidents and findings during delivery

- **Enrollment resets open connections.** When a pod is captured, some of its open connections are cut:
  - each service's Postgres pool: 1–3 s of `connection has been closed` and failed outbox polls;
  - the adapter's SFTP session to the ERP: one failed poll, then reconnected;
  - notification's Kafka producer: one retried send.

  Everything recovered by itself. Backlog, needs-attention, quarantine and outbox gauges stayed at 0, and no new alert fired. Some older pooled DB connections were left open and bypass ztunnel until recycled.
- **CRD ownership race.** The ingress operator rewrote `gateways.networking.istio.io` in the moment between OLM applying it and labelling it. Its code otherwise yields to OLM-managed CRDs. This was stable after install.
- **First control-plane sync failed once.** The `Telemetry` reached istiod's webhook before istiod had endpoints, because Argo has no health check for the `Istio` CR. A re-sync fixed it, and #96 added a sync retry.
- **Kiali missed later namespaces.** The operator evaluates `discovery_selectors` only when it reconciles and does not watch labels, so the first enrolled namespace was invisible. #96 switched to an explicit namespace list.
- **Waypoints had no tracing.** istiod could not resolve `box1-collector`, because the discovery selector excluded `box1-observability`. #98 labelled that namespace for discovery only.
- **The top `unknown` node in Kiali** is traffic from outside the mesh, mostly user-workload Prometheus scrapes. The bytes sent back per scrape interval matched each service's `/q/metrics` size.

## Final operational state

As last observed on 2026-11-06 at 23:19 EST. The cluster was **not re-verified** when this log was written on 2026-11-08: the `oc` session had expired.
- **Managed by Argo CD from `box1-gitops` `main`** (manual sync), all Synced/Healthy at last check:
  - `service-mesh-network`, `service-mesh-operators`, `service-mesh-control-plane` and `service-mesh-kiali`;
  - `observability-tracing` (now carrying the discovery label).
- **Managed from `box1-workloads-dev` `main`** (auto-sync): the namespace labels, waypoints, tracing Telemetry, PodMonitors and Postgres NetworkPolicies.
- **Not managed by Argo:** the Kiali operator's generated roles and the istiod-generated waypoint Deployments, which their operators own.
- **Waypoint requests** are the template defaults (100m / 128 MiB). Lowering them to about 10m / 64 MiB would free about 270m CPU of requests. Not done.

## Recovery

- **One namespace out of the mesh:** remove `istio.io/dataplane-mode`, `istio-discovery` and, where present, `istio.io/use-waypoint` from its `workloads/<service>/namespace.yaml`. Argo self-heals. Expect the same few-second DB, SFTP and Kafka reset. **Untested.**
- **L7 only:** remove `istio.io/use-waypoint`; the namespace stays L4.
- **Waypoint tracing:** remove `istio-discovery` from `box1-observability`.
- **Whole mesh:**
  1. un-enroll all namespaces;
  2. delete `Kiali`, `ZTunnel`, `IstioCNI` and `Istio`, then the Applications;
  3. delete the Subscriptions and CSVs. CRDs remain.
- **Local gateway mode:** delete `service-mesh-network`, then set `routingViaHost: false`. This restarts `ovnkube-node` again. **Untested.**

## Follow-ups

- **Criterion 1, rollback:** [box1-workloads-dev#150](https://github.com/box1-org/box1-workloads-dev/pull/150) is open, deferred by the user, and now conflicts with #152. It must also remove `use-waypoint`.
- **Criterion 4:** the NetworkPolicy baseline on DB, Kafka and ERP paths, under ambient. Default-deny needs its own approval.
- **Waypoint scope** for the other four namespaces: the user's decision. Decision 006 recommends none.
- **Optional:** lower the waypoint resource requests; investigate Kiali's `Multiple workloads found for GatewayAPI waypoint` warning.
- **The run-state branch** `agent-run/23-ambient-mesh` is not merged.

Related logs: [observability](2026-11-06-observability-tracing-metrics.md) (#22), which supplies the Tempo, collector and monitoring this run builds on.
