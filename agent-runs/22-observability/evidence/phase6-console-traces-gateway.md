# Console Traces view (COO) and Tempo gateway RBAC: delivery (2026-11-06)

User approvals in chat:
- "lets try COO … Can we keep both?" (decision 007, gateway option chosen);
- "Yes, merge and sync";
- "Grant via GitOps PR" (Argo tokenreviews).

## Delivery
- **box1-gitops#87:** merged as `ec16dc3e`. It added the COO, the UIPlugin, Tempo multitenancy, collector auth, trace RBAC and NetworkPolicies, after an independent review and a server dry run.
- **COO:** `observability-operators` synced. InstallPlan `install-4btrv` contained only `cluster-observability-operator.v1.5.5`; it was approved and the CSV reached `Succeeded`. The CRD `uiplugins.observability.openshift.io` was created.
- **First tracing sync (step 1: RBAC + TempoMonolithic) was rejected** by the Tempo webhook:
  > Cannot enable OpenShift tenancy mode: user …argocd-application-controller does not have permission to create tokenreviews.authentication.k8s.io

  The webhook (`validateGatewayOpenShiftModeRBAC`) requires the applier to already hold what the gateway SA will get. Tempo stayed unchanged and ingest continued (send_failed none). The three trace ClusterRoles were created.
- **box1-gitops#88:** ClusterRole `box1-observability-argocd-tokenreview` (`create tokenreviews` only), bound to the Argo controller. Merged as `f6c57b16`.
- **Step 1 retry:** Succeeded.
  - Pod `tempo-box1-0` now has the containers `tempo`, `tempo-gateway`, `tempo-gateway-opa`, `jaeger-query` and `tempo-query`. The OAuth proxy is removed. 0 restarts.
  - Service `tempo-box1-gateway`: public 8080, internal 8081, http 3200, otlp-grpc 4317 → grpc-public.
  - Route `tempo-box1-jaegerui` → `tempo-box1-gateway:public`, reencrypt.
  - PVC `tempo-storage-tempo-box1-0` kept (same volume).
- **Step 2 (full sync, collector wave 1, NetworkPolicies wave 2):** Succeeded at about 22:08Z. The collector rolled to `box1-collector-5bcdc959c5-jzqlw` with no auth or connection errors. `observability-tracing` is Synced/Healthy.
- **`observability-console`:**
  - It was first synced at 22:01:33Z by "mike" (outside this run, at `ec16dc3`), then by this run at `f6c57b16`. Synced/Healthy.
  - UIPlugin `distributed-tracing`: Reconciled, Available. Pod `distributed-tracing-54cb976bc6-xc7dz` is running. ConsolePlugin `distributed-tracing-console-plugin` is enabled in the console.

## Checks
| Check | Result |
|---|---|
| New order `ord_d036f901bca941a3a4fd73763674e03b` (trace `aa4f7efc117e3b1e8b160568b4e26725`), read through the gateway with the operator's token as tenant `dev` | HTTP 200; spans from order, inventory and notification present at read time |
| The same read, anonymous | 302 to OpenShift login |
| Jaeger UI `/api/traces/v1/dev/search`, anonymous | 302 → `/openshift/dev/login` |
| Jaeger UI API with token: services | 200; 6 services listed (scenario-controller had no traffic since the switch) |
| Anonymous `/` on the gateway Route | 200 with only a path index (no data); all data paths answer "failed to find token" |
| SubjectAccessReview `tempo.grafana.com/dev`, name `traces` | collector: create **true**, get **false**; `box1-observability:default`: create/get **false**; `order-service-dev:order-service`: create/get **false**; the operator (cluster-admin): get **yes** |
| Collector after the switch | `otelcol_exporter_sent_spans` increasing, no `send_failed` series |
| ClusterOperators console and monitoring | Available, not Degraded |

**Not verified by this run:** the Observe → Traces page in a browser. The plugin backend uses the signed-in user's token; the user has to look.

## Footprint (idle)
| Pod | Memory |
|---|---|
| tempo-box1-0 | 136Mi |
| collector | 53Mi |
| distributed-tracing plugin | 14Mi |
| COO operator and admission webhooks | about 120Mi |
| COO monitoring plugin | 13Mi |
| perses and perses-operator | 73Mi |

## Unplanned side effect
On install, the COO created UIPlugin `monitoring` (21:56:25Z, not Argo-tracked, not in Git). That deployed `monitoring-console-plugin` (enabled in the console) and `perses` / `perses-operator`. Not changed by this run; needs a user decision: adopt it into Git, or delete it.

## Data visibility
Traces written before the switch (single-tenant) are not visible through the gateway; they expire with the 72 h retention.

## Correction: owner of UIPlugin `monitoring`

The earlier note above attributed it to the COO. That was wrong.

- **Owner:** the UIPlugin carries `platform.kubevirt.io/managed-by: virt-platform-autopilot`.
- **What the autopilot did:** `openshift-cnv/virt-platform-autopilot` started watching UIPlugins at 21:56:07Z and applied asset `monitoring-ui-plugin` at 21:56:25Z. It keeps reconciling it ("No drift detected, skipping apply").
- **User decision:** keep it and document it in Git without Argo management. The ownership choice was put to the user with the trade-offs.
- **Delivery:** box1-gitops#89 (README only); checks passed. **Not merged:** the merge was blocked for lack of explicit approval and is left to the user.
- **Not established:** a supported HyperConverged switch to turn it off.
