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
