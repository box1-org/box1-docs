# Phase 6/7: service builds and the order-service trace (2026-11-06, America/New_York)

User approval in chat: "Yes, merge them all". That covered the seven service PRs and box1-workloads-dev#119. After the promotion failures below, the user directed: "lets try again with just the order-service for now."

## Seven service merges (about 15:17 EST)

All seven `trace-export-build` PRs were squash-merged at their checked heads. Each release build and security task **succeeded**. The promote step then failed for three services: three promotion PRs (fulfillment-adapter #122, notification #123, asset #126) had their `box1-gitops-validate` and `box1-phase1-smoke` runs **Cancelled** by Pipelines as Code while seven promotions ran at once. The promote task asserts that the required checks succeeded, so it failed with:

`AssertionError: Required GitOps check failed: Pipelines as Code CI / box1-gitops-validate-`

| Service | Source merge | Release | Promotion | Running digest |
|---|---|---|---|---|
| order-service | 64362af | Succeeded | #120 merged | sha256:5e4e66f6ba3c |
| inventory-service | 646bd02 | Succeeded | #121 merged | sha256:ccc4b910d1aa |
| scenario-controller | 23125f8 | Succeeded | #124 merged | sha256:0607f1f89cf7 |
| operations-console | 96f4a97 | Succeeded | #125 merged | sha256:4c67128a2006 |
| fulfillment-adapter | 5f1d5fd | promote failed | #122 open, checks cancelled | unchanged, sha256:dd19f34b0a1d |
| notification-service | 24dda0f | promote failed | #123 open, checks cancelled | unchanged, sha256:69788422d2f3 |
| asset-service | 0bfca82 | promote failed | #126 open, checks cancelled | unchanged, sha256:4ece8230d156 |

All four promoted services were 1/1 ready with 0 restarts after rollout. In the 10 minutes after rollout, their logs had no ERROR lines, no OTLP errors and no `VertxTracer delegate not set` warnings; export was still off at sampler ratio 0.0. The pre-change count of that warning was not measured for these four services. #61 had observed it on asset-service, which has not been promoted.

## Order-service export (box1-workloads-dev#119, order-service only)

- #119 was rebuilt on current main to change only `workloads/order-service`, then squash-merged as `b8513c13e3a36399b893a26370707a3177be6d20` after `box1-gitops-validate` and `box1-phase1-smoke` passed.
- Argo rolled the pod `order-service-7fd58974dc-g7sf9`: ready, 0 restarts, ConfigMap `order-service-config-84tf2gkbf9` with `QUARKUS_OTEL_TRACES_SAMPLER_ARG=1.0`.
- The Application shows `OutOfSync` only for the previous generated ConfigMap `order-service-config-8btd4c24mh`. This Application does not prune.

## End-to-end check

`POST https://order-service-dev.apps.ocp.box1.org/api/v1/orders` with a client `traceparent`, trace ID `836eac165e3b63aeca14a4597c8d15c5`:

- **Order:** 201, `orderId=ord_b78f7a00585b44bd931ba310b4aba301`. The response `traceId` equals the trace ID sent.
- **Order state:** `FULFILLMENT_REQUESTED` / `INVENTORY_RESERVED`, so the business flow completed through inventory.
- **Tempo** `GET /api/v2/traces/836eac16…` returned two order-service spans:

  | Kind | Span | Duration |
  |---|---|---|
  | SERVER | `POST /api/v1/orders` | 21 ms |
  | INTERNAL | `order.consume inventory.reserved.v1` | 8 ms |

  inventory-service exports nothing (ratio 0.0), but it carried the trace ID through Kafka and back. The order consumer therefore joined the same trace.
- **JSON logs** for the order ("Order created" and "Event applied: states=[RESERVED, FULFILLMENT_REQUESTED]") include `traceId=836eac16…`, `orderId` and `correlationId`. This is the orderId → traceId lookup path.
- **Collector (UWM):** `otelcol_receiver_accepted_spans` = 8 + 1 and `otelcol_exporter_sent_spans` = 9. No `send_failed` series exists.
- **order-service log**, 5 minutes after rollout: 0 ERROR lines, 0 exporter errors, 0 VertxTracer warnings.

## Not established
- Inventory and adapter spans: their export is not on.
- Outbox and Kafka publish spans: none are emitted by the code.
- Behaviour during a collector outage: not exercised.

## Inventory-service export (box1-workloads-dev#127)

User approval in chat: "Yes, inventory next".

- #127 changed only `workloads/inventory-service`. It was squash-merged as `be0d527ae281aa9ea6a635261003bb20f9fb84e7` after `box1-gitops-validate` and `box1-phase1-smoke` passed.
- Pod `inventory-service-99c68ddf7-h8blm`: ready, 0 restarts, ConfigMap `inventory-service-config-9mm646ftfk` with ratio 1.0. Image source `646bd02`, `sha256:ccc4b910d1aa`.

**Sample order:** `ord_348064921994474291ba11fd1a47785a`, trace ID `4d2f417360e14a3d26cc08f98d15b462`. POST returned 201; the order reached `FULFILLMENT_REQUESTED` / `INVENTORY_RESERVED`.

**Tempo returned one connected trace.** Each span's parent is the previous span:

| # | Service | Kind | Span | Duration |
|---|---|---|---|---|
| 1 | order-service | SERVER | `POST /api/v1/orders` | 8 ms |
| 2 | inventory-service | INTERNAL | `inventory.consume order.placed.v1` | 18 ms |
| 3 | order-service | INTERNAL | `order.consume inventory.reserved.v1` | 5 ms |
| 4 | inventory-service | INTERNAL | `inventory.consume order.state-changed.v1` | 2 ms |

**Logs:** the JSON lines in both services carry, under `mdc`, `traceId=4d2f417360e14a3d26cc08f98d15b462`, `sampled=true`, `orderId` and `correlationId`; inventory also carries `eventId` and `eventType`. (This corrects the earlier note: the fields live under `mdc`, not at the top level.)

**Health and collector:** in the 10 minutes after rollout, the inventory log had 0 ERROR lines, 0 exporter errors and 0 VertxTracer warnings. Collector totals: `otelcol_receiver_accepted_spans` = 16, `otelcol_exporter_sent_spans` = 16, no `send_failed` series.

**Still missing:** the fulfillment-adapter boundary. Its promotion (#122) failed, its Kafka consumer creates no span (decision 005), and it has no Camel tracing.

## Fulfillment-adapter promotion and export (2026-11-06)

User approval in chat: "Yes, adapter next", meaning re-run its promotion, then turn on export.

- **Promotion #122:** `/retest` re-ran the cancelled checks; `box1-gitops-validate` and `box1-phase1-smoke` passed on head `a24499c`. Squash-merged as `60c8bae64128641737b2625a0f921311865db8ff`. Pod rolled to `sha256:db35db9e8625` (source `5f1d5fd`), ready, 0 restarts.
- **Export #128:** squash-merged as `03f77b8ff7762c664c29e6e59ceaac652f920916` after checks passed. Pod `fulfillment-adapter-f98b9d897-5v9p4` is ready, 0 restarts, with sampler ratio 1.0.
- **Sample order** `ord_b587860f32824335a44e01d8c575d391` (trace `36dc7ff9274aa0a4abae9f54d1445768`) reached `FULFILLMENT_REQUESTED`. The adapter created `ful_b587860f…` and uploaded the request file.
  - Tempo shows the order and inventory spans, including `inventory.consume fulfillment.requested.v1`.
  - **There is no adapter span.** The adapter's log lines for the order have no `traceId`, because its Kafka consumer creates no span (decision 005).
  - The adapter logged 0 ERROR lines and 0 exporter errors.
- **Code fix:** [box1-org/fulfillment-adapter#5](https://github.com/box1-org/fulfillment-adapter/pull/5) adds a CONSUMER span parented on the envelope `traceparent`. Local `./mvnw -B verify`: 103 tests passed, 0 Checkstyle violations, 0 SpotBugs bugs. Not merged; needs approval.
- **Observation:** Tempo's `/api/v2/traces/{id}` returned the `POST /api/v1/orders` span twice, with the same span ID `EbH6WqiLocY=`. This is a read-side duplicate, likely the same span in both the live ingester data and a flushed block. It is not a second request.

## Adapter consumer span (fulfillment-adapter#5): end-to-end trace through three services

User approval in chat: "Yes, merge #5".

- **Merge:** fulfillment-adapter#5 was squash-merged as `efa4f1e8223a6beed194554e9d17b485196f98d8` after `fulfillment-adapter-validate` passed on head `ee491e1`.
- **Release** `fulfillment-adapter-release-l769j`: build and security Succeeded. Promotion #129 auto-merged at `36d0b30f`.
- **Rollout:** the pod `fulfillment-adapter-74bdd7598f-gvh59` runs source `efa4f1e`, `sha256:15aa4ef32b02`; ready, 0 restarts.
- **Promote step failed** after deployment with `TimeoutError: ... expected GitOps revision=36d0b30f, observed revision=36d0b30f, sync=OutOfSync, health=Healthy`. The only OutOfSync resource is the orphaned `ConfigMap/fulfillment-adapter-config-89db8g96gh` (requiresPruning), left by the export ConfigMap change in #128. This is the known [#42](https://github.com/box1-org/box1-docs/issues/42) item 2. The deployment is correct; the release run is red.
- **Orphans on the other exporting services** at this time: order-service OutOfSync ConfigMap/order-service-config-8btd4c24mh;inventory-service OutOfSync ConfigMap/inventory-service-config-cb8h282db5;

**Sample order** `ord_ebae01715c30481ca38883cd38ade947`, trace `113f8a68c7791743bc3a83f46c58f3c3`. The order reached `SHIPPED` / `SHIPMENT_CONFIRMED` (ERP in AUTO mode).

Tempo trace, unique spans in start order:

| Service | Kind | Span | Parent |
|---|---|---|---|
| order-service | SERVER | `POST /api/v1/orders` | client |
| inventory-service | INTERNAL | `inventory.consume order.placed.v1` | POST |
| order-service | INTERNAL | `order.consume inventory.reserved.v1` | inventory |
| inventory-service | INTERNAL | `inventory.consume order.state-changed.v1` | order consume |
| inventory-service | INTERNAL | `inventory.consume fulfillment.requested.v1` | order consume |
| **fulfillment-adapter** | **CONSUMER** | **`fulfillment.consume fulfillment.requested.v1`** | order consume |
| inventory-service | INTERNAL | `inventory.consume order.state-changed.v1` | order consume |
| order-service | INTERNAL | `order.consume shipment.confirmed.v1` | order consume |
| inventory-service | INTERNAL | `inventory.consume shipment.confirmed.v1` | order consume |
| inventory-service | INTERNAL | `inventory.consume order.state-changed.v1` | order shipment consume |

The adapter span attributes are `box1.order_id=ord_ebae01715c30481ca38883cd38ade947`, `box1.fulfillment_request_id=ful_ebae0171…` and `box1.acceptance_result=CREATED`.

The ERP hop is not traced. The ERP result events carry the stored order `traceparent`, so `shipment.confirmed` consumers stay in the same trace. Inside the ERP, correlation is by `fulfillmentRequestId` (prompt rule).

**orderId → trace through logs:** `oc logs` lines for the order carry `mdc.traceId=113f8a68c7791743bc3a83f46c58f3c3`, `orderId` and `correlationId` in:
- order-service: "Order created", "Event applied: … FULFILLMENT_REQUESTED", "Event applied: … SHIPPED";
- inventory-service: "Event reserved", "Event committed";
- fulfillment-adapter: "Fulfillment request created".

The adapter's async "Uploaded request file" line has `orderId` but no `traceId`, because it runs in the dispatch worker outside a span.

**Health:** no ERROR lines and no exporter errors in the three services in the last 10 minutes. Collector: accepted 145, sent 145, no `send_failed`. Tempo `/var/tempo` is 1.1M of 10Gi.
