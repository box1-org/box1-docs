# Metrics, alerts and dashboard: delivery (2026-11-06)

User approvals in chat: "Lets do metrics and alert"; "Yes, merge and sync".

## Delivery
- **box1-workloads-dev#138:** squash-merged at 22:31:07Z as `210c25f4`. 7 ServiceMonitors and 7 PrometheusRules.
- **box1-gitops#90:** merged 15 s later (22:31:22Z) as `69887463` (box1-docs#64 spacing).
- **Workload apps:** all seven auto-synced to Synced/Healthy. No pod restarts, no ConfigMap changes.
- **`observability-dashboards`:** synced to Synced/Healthy.
  - PersesDatasource `box1-thanos-querier`: Available ("created successfully").
  - PersesDashboard `box1-order-flow`: Available.
  - The Perses server stored `secrets/box1-observability/box1-thanos-querier-secret.yaml` and `dashboards/box1-observability/box1-order-flow.yaml`.

## Scraping
`up{job=<service>}` = 1 in Thanos for all seven: order, inventory, fulfillment-adapter, notification, asset, scenario-controller and operations-console.

## Dashboard data
All 17 panel queries return series through the Thanos querier. Values at about 22:33Z:

| Panel | Value |
|---|---|
| Oldest open order | 116,592 s (~32 h) |
| Stuck orders | 2 |
| Order outbox pending | 0 |
| ERP unacknowledged / backlog / awaiting operator / needs attention | 0 / 0 / 0 / 0 |
| ERP results | APPLY |
| Uploads | FIRST, uploaded |
| Quarantined files | 0 |
| `up` | 7 series |

**Not verified by this run:** the dashboard rendering in the console.

## Alert path
- `Box1OrdersStuck` (2 pre-existing stuck orders, the oldest about 32 h): pending, then **firing at 22:38:40Z**. The platform Alertmanager lists it **active** (namespace `order-service-dev`). This proves the rule → user-workload Prometheus (leaf) → Alertmanager path.
- No other Box1 alert was active.

## Normal AUTO acknowledgement baseline
- Three orders placed 20 s apart: `ord_72fde75b…`, `ord_a1116d48…`, `ord_71805d12…` (22:35:08–22:35:48Z). Each reached SHIPPED in **5.2 s, 7.1 s and 7.1 s**.
- Over 10 minutes (17 samples), `max_over_time(fulfillment_oldest_unacknowledged_seconds)` = 0 and `max_over_time(fulfillment_backlog)` = 0. `Box1ErpAcknowledgementDelayed` did not fire. With the 15 s gauge refresh, sub-15-s acknowledgements never show in the gauge.
- **Earlier slow order explained:** `ord_79c7a107…` (21:30Z) was **acknowledged in 2 s** (ERP result revision 1, status PENDING at 21:30:49). It then waited about 2 min until three requests were released together at 21:32:54. That is ERP MANUAL/hold behaviour: `Box1ErpAwaitingOperator` territory, not an acknowledgement delay. It is not a false positive for the 30 s rule. The source of the MANUAL period was not identified.

## Not yet established (criterion 2 stays open)
- **Alert latency** of `Box1ErpAcknowledgementDelayed` from an ERP stall, and of `Box1ErpAwaitingOperator` from a MANUAL backlog, against the under-2-minute target. This needs an ERP stall or MANUAL mode, which is fault injection and needs approval.
- **Adapter gauge bug:** `fulfillment_oldest_unacknowledged_seconds` includes NEEDS_ATTENTION rows (adapter `FulfillmentStore.java:490`).
