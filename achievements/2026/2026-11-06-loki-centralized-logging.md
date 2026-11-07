# Centralized logging: LokiStack on NooBaa, with Box1 service logs in Observe → Logs

**Date:** 2026-11-06 (America/New_York), about 23:20–23:59 EST. Cluster timestamps below are UTC on 2026-11-07.

**Status:** Delivered and live. Acceptance is partial. [box1-docs#82](https://github.com/box1-org/box1-docs/issues/82) stays open with 7 of 9 checklist items ticked, each with cluster proof ([evidence comment](https://github.com/box1-org/box1-docs/issues/82#issuecomment-6702513079)). Two items are open:
- opening a trace's logs from the trace UI;
- a steady-state storage measurement over a full retention window.

Background: tracing, metrics and the earlier decision to defer logging are recorded in [2026-11-06-observability-tracing-metrics.md](2026-11-06-observability-tracing-metrics.md).

## Outcome

Logs from the seven Box1 services are now collected centrally, kept for 3 days, and searchable in the OpenShift console under **Observe → Logs** and through LogQL.

- **Order lookup works.** One query by `orderId` returns that order's lines from order, inventory, the fulfillment adapter and notification.
- **Trace lookup works by trace ID.** A query by `traceId` returns the same lines.
- **Logging is off the business path.** The order flow kept working while Loki was down, and no log lines were lost.
- **Storage choice.** The user chose LokiStack on a dedicated NooBaa bucket and accepted the risk that NooBaa can go offline after a node eviction ([#43](https://github.com/box1-org/box1-docs/issues/43)).

| Item | Value |
|---|---|
| Operators (OLM, manual InstallPlans, GitOps-managed) | Loki Operator `loki-operator.v6.7.0` (channel `stable-6.7`, namespace `openshift-operators-redhat`); Red Hat OpenShift Logging `cluster-logging.v6.7.0` (`stable-6.7`, `openshift-logging`) |
| Log store | `LokiStack/logging-loki` in `openshift-logging`. Size `1x.demo`, retention 3 days, tenant mode `openshift-logging`, schema `v13` |
| Object storage | ObjectBucketClaim `logging-loki` (generated bucket `box1-logging-loki-*`) on `openshift-storage.noobaa.io` |
| Local storage | 4 × 10 Gi PVCs on `lvms-vg1`: ingester, WAL, compactor, index gateway |
| Collector | Vector `ClusterLogForwarder/box1`, service account `logcollector`. Application logs only, from `order-service-dev`, `inventory-service-dev`, `fulfillment-adapter-dev`, `notification-service-dev`, `asset-service-dev`, `scenario-controller-dev` and `operations-console-dev` |
| Console | UIPlugins `logging` (Observe → Logs) and `troubleshooting-panel` (korrel8r) |
| GitOps | `box1-gitops` Application `observability-logging` (new, manual sync, `platform/observability/logging/`); `observability-operators` and `observability-console` extended |

## Starting baseline

These are read-only observations from 2026-11-06, before any change:

- **Cluster and logging:** OpenShift `5.0.0-rc.7` on the single node `quark`. No logging or Loki operator was installed. Services wrote structured JSON logs that could only be read with `oc logs` or the console pod view.
- **Node budget:** 75% of CPU and 70% of memory already requested. `1x.pico`, the smallest supported LokiStack size, requests about 7.5 vCPU, so only `1x.demo` fits. `1x.demo` sets no CPU or memory requests.
- **Storage:** about 78.5 GiB free on `lvms-vg1` (thin pool, `overprovisionRatio: 1`).
- **NooBaa:** `Ready`, one `pv-pool` backing store (`noobaa-default-backing-store`, `OPTIMAL`). Its earlier 4.4-day silent outage after an eviction is recorded in #43. The only existing ObjectBucketClaim was TPA's.
- **Catalog:** the catalog listed `cluster-logging` `stable-6.6` (6.6.1) and `loki-operator` `stable-6.7` (6.7.0). Within the hour, the catalog changed to offer only `cluster-logging.v6.7.0` (see below).

## What changed

| PR | Merge | Change |
|---|---|---|
| [box1-gitops#100](https://github.com/box1-org/box1-gitops/pull/100) | `5843832` | Loki Operator and Logging Subscriptions. New `observability-logging` Application: Argo CD Role, OBC, credential sync Job, LokiStack, collector service account and ClusterRoleBindings, ClusterLogForwarder. `logging` and `troubleshooting-panel` UIPlugins. README section |
| [box1-gitops#101](https://github.com/box1-org/box1-gitops/pull/101) | `b6cf68f` | Logging channel `stable-6.6` → `stable-6.7`. The subscription had failed with `ResolutionFailed: no operators found in channel stable-6.6`: the v5.0 catalog now ships only `cluster-logging.v6.7.0`. This also matches the Loki Operator version |
| [box1-gitops#102](https://github.com/box1-org/box1-gitops/pull/102) | `3579318` | Docs only: corrects the trace-to-log guidance. The panel does not link Box1 traces to logs; use a console deep link by `traceId` instead |

The user approved each merge in chat.

**Design decisions:**

- **No credentials in Git.** NooBaa writes the bucket's keys into a Secret and ConfigMap named `logging-loki`. A sync-hook Job, `logging-loki-s3-sync`, runs on every sync of `observability-logging` and copies them into Secret `logging-loki-s3`, in the format LokiStack expects.
  - The Job, not Argo CD, owns that Secret.
  - The Job's Role allows only reading `logging-loki` and writing `logging-loki-s3`.
  - Its image is the cluster's `openshift/cli` release image, pinned by digest (`ocp-v5.0-art-dev@sha256:bba4bac…`).
- **TLS to NooBaa** uses the OpenShift service CA (`openshift-service-ca.crt`).
- **The bucket survives app deletion.** The OBC has `Prune=false,Delete=false`, so deleting the Application keeps the stored logs.
- **Redaction is a backstop.** The services redact at source (#22). The forwarder's `drop-credentials` filter drops any line matching a bearer token, password, client secret or private-key pattern. A dropped line is lost.
- **Parsed fields.** The `parse` filter turns each JSON line into `structured`, so `| json` exposes fields such as `structured_mdc_orderId`, `structured_mdc_traceId` and `structured_message`.
- **Narrow collection.** Only the seven service namespaces are collected; infrastructure and audit logs are not. Plain-text istio-proxy lines in those namespaces are collected unparsed.

**Made outside Git, with the user's approval:**
- Argo syncs of `observability-operators` (twice), `observability-logging` and `observability-console`, each triggered by setting the Application `operation`.
- InstallPlan approvals after checking each CSV name: `install-q47gx` (`loki-operator.v6.7.0`) and `install-xz9d8` (`cluster-logging.v6.7.0`).
- The outage test below: a temporary `managementState: Unmanaged` and scale-down, then reverted.

## Validation and evidence

All checks ran against the live cluster through the LokiStack gateway Route `logging-loki-openshift-logging.apps.ocp.box1.org`, with a cluster-admin token.

| Check | Result |
|---|---|
| Rollout | LokiStack `Ready=True`; all 9 Loki pods and the collector running. ClusterLogForwarder `Authorized=True` (application logs), `Valid=True`, `Ready=True`. All three Applications `Synced` / `Healthy` |
| Query by `orderId` | `{log_type="application"} \|= "ord_2f6bb653158242adbc3bfa81b6ccb4d7"` returned order-service 3, inventory-service 6, fulfillment-adapter 2 and notification-service 7 lines |
| Query by `traceId` | `\| json \| structured_mdc_traceId="8670e0b4e7e2ac6b40fd9f86b76e77ea"` returned 17 of those lines, across the same four services |
| Ingest outage | 04:53:58Z: LokiStack set to `Unmanaged`, distributor and gateway scaled to 0. Queries returned 503 and Vector logged retries. Order `ord_5edbc51bd1274eff94f07e0619df5cde`: POST **201 in 28 ms**, `SHIPPED` within about 10 s. Restored and back to `Managed` by 04:54:34Z |
| No loss across the outage | The outage order and the baseline order `ord_ff6ea244ebf3405cacb798bb232f652d` each have 18 lines across 4 services after recovery |
| Log audit | 604 lines from all 7 namespaces scanned for bearer tokens, JWTs, password/secret/API-key pairs, AWS keys, private keys, emails and phone numbers. No credentials and no customer personal data; customers appear only as IDs such as `cust_demo_kai`. The one email-pattern hit is the SFTP service account in a connection URI, with no password. The one `authorization` hit is Quarkus's OIDC startup warning, which contains no secret value |
| Retention | Loki config: `retention_enabled: true`, `retention_period: 3d`, `delete_request_store: s3` |
| Footprint, about 10 minutes after start | WAL 3.9 MiB (604 lines, about 2.1 MB of JSON). RAM: Loki pods and collector together under 700 MiB, cluster-logging operator 150 MiB, Loki operator 305 MiB. CPU under 0.1 core in total. topolvm free space dropped from 84.3 GB to 41.4 GB, because the four PVCs are fully committed |

**Not tested or not established:**

- **Trace → logs from the trace UI** ([#82](https://github.com/box1-org/box1-docs/issues/82) criterion). The distributed-tracing plugin has no logs link. The troubleshooting panel's korrel8r trace store is fixed by the operator to `tempo-platform` in `openshift-tracing`, which does not exist here, and the UIPlugin does not expose that setting. Its trace rules lead only to Pods.
  - What works: the console deep link `/monitoring/logs?tenant=application&q=<LogQL>`. Its `q` and `tenant` parameters were confirmed in the plugin source.
  - The console was not opened in a browser, because the agent's permission policy blocked it.
- **Steady-state footprint:** daily volume and bucket size over a full 3-day window were not measured.
- **NooBaa outage:** only Loki ingest was taken down. NooBaa's backing store going offline was not exercised.
- **Whether `drop-credentials` fired:** not measured.
- **Vendor support:** `1x.demo` is not supported for production. Vendor support for Loki/Logging 6.7 on OpenShift 5.0.0-rc.7 is not established.

## Final operational state

- **Management:** Argo CD runs `observability-operators`, `observability-logging` and `observability-console` from `box1-gitops` `main` (`3579318`), with manual sync. There is no manual override; the outage-test changes were reverted.
- **Reading logs:** cluster admins see all collected logs. Other users see application logs for namespaces they can view (tenant mode `openshift-logging`).
- **Query syntax:** show only the message and pod for a trace:

  ```logql
  {log_type="application"} | json | structured_mdc_traceId="<traceId>" | line_format "{{.kubernetes_pod_name}}: {{.structured_message}}"
  ```

- **Known risk:** if NooBaa's backing store goes offline again (#43), the ingesters cannot flush and older logs cannot be queried. The collector buffers, retries, and eventually drops. Orders and fulfillment are unaffected.
- **Upgrade caveat:** the sync Job's image digest is tied to 5.0.0-rc.7. Update it after a cluster upgrade, or the next sync may fail to pull it.

## Recovery and follow-ups

- **Stop collection:** delete `ClusterLogForwarder/box1`.
- **Remove the stack:** delete the `observability-logging` Application with cascade. This deletes the LokiStack PVCs. Then delete OBC `logging-loki` and Secret `logging-loki-s3` by hand to remove the bucket and its data. Remove the two UIPlugins from `platform/observability/console/`.
- **Remove the operators:** delete the CRs first, then the Subscriptions and CSVs.
- None of these paths was exercised. Full steps are in [`platform/observability/README.md`](https://github.com/box1-org/box1-gitops/blob/main/platform/observability/README.md).
- **Follow-up:** one-click trace → log navigation. Options: a COO release that lets korrel8r's trace store be configured, or a trace-link pattern in a trace UI ([#82](https://github.com/box1-org/box1-docs/issues/82)).
- **Follow-up:** measure daily ingest, bucket size and PVC use after 3 days, then record them on #82.
- **Follow-up:** NooBaa eviction recovery and alerting ([#43](https://github.com/box1-org/box1-docs/issues/43)).
