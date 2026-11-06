# 008 Metrics, alerts and dashboard (criterion 2)

**Scraping:** ServiceMonitors in each service's `box1-workloads-dev` directory, scraped by user-workload monitoring. The adapter is scraped every 15 s, the others every 30 s. No service code changes: the metrics already exist.

**Alerts:** PrometheusRules in the namespace that owns the metrics. User-workload rules see only their own namespace. Rules use `leaf-prometheus` evaluation, which avoids Thanos Ruler lag.
- **ERP delay:** `Box1ErpAcknowledgementDelayed`, oldest unacknowledged request > 30 s for 15 s, 15 s evaluation. About 90 s worst case from acceptance; must be measured.
- **MANUAL backlog:** `Box1ErpAwaitingOperator` > 0 for 2 m.
- **Also:** needs attention, quarantined files, stale gauges, stuck orders (order-service definition: 900 s), order outbox delay, inventory DLQ, and `Box1ServiceDown` for all seven services.

**Dashboard:** Perses, because that is the console's direction and OpenShift Virtualization already uses it on this cluster.
- PersesDashboard `box1-order-flow` in `box1-observability`.
- Default PersesDatasource `box1-thanos-querier`, copying the openshift-cnv pattern.

**Known gaps:**
- **Firing baseline:** `Box1OrdersStuck` fires on two pre-existing stuck orders.
- **Adapter bug:** `fulfillment_oldest_unacknowledged_seconds` includes NEEDS_ATTENTION rows (`FulfillmentStore.java:490`), so one such row masks new ERP stalls. Follow-up in the adapter repo.
- **Not measured:** normal AUTO acknowledgement latency and alert latency. Measuring alert latency needs a MANUAL-mode or stalled ERP, which is fault injection and needs approval.
- **Not tuned:** gauge refresh is 15 s; lowering it to 5 s would be a ConfigMap change (restart and orphan prune).

**Delivery:** box1-workloads-dev#138 and box1-gitops#90.
