# Enrollment 2: order-service-dev and inventory-service-dev (2026-11-06 America/New_York)

**Change:** [box1-workloads-dev#148](https://github.com/box1-org/box1-workloads-dev/pull/148), squash-merged at the user's instruction as `5b596ce` (22:39:06 EST). Argo auto-synced both Applications by 22:39:12.

## Capture
- Ztunnel logged `starting proxy` for all four pods: order, order-postgres, inventory and inventory-postgres.
- All four pods have `ambient.istio.io/redirection: enabled`, are ready, and have no new restarts. The Postgres restart counts (2) date from 2026-11-05.

## Effect on existing database connections (finding)
- When the Postgres pods were captured, **some existing pooled connections were closed**. Between 03:39:13 and 03:39:15Z, order logged 2 and inventory 3 `Datasource … This connection has been closed` warnings. Each came with an `ARJUNA016045` rollback and an `Outbox poll failed: StoreException`.
- The outbox pollers retry every second, and the pools reconnected. There were no warnings after 03:39:15Z, and no Kafka consumer errors.
- Other pre-enrollment connections stayed open (`pg_stat_activity` backends from 20:26 and 23:00 UTC). They bypass ztunnel until the pool recycles them.
- **Implication:** enrolling or un-enrolling a namespace with a database causes a few seconds of failed DB calls. The outbox design absorbs it; synchronous API calls in that window may return errors (not measured).

## Business flow
Order `ord_a20bf36598cc4c05a263407085184f24` reached SHIPPED in about 6 s (trace `dc1e311f73ba5f7dfb29a89ccb81c073`). From inside the console pod, 3 of 3 calls each to order and inventory returned 200.

## mTLS (MESH-MTLS-001)
- **Thanos**, `istio_tcp_connections_opened_total`, `connection_security_policy="mutual_tls"`, reported by both source and destination:
  - `operations-console → order-service` and `→ inventory-service`;
  - `order-service → order-service-postgres` (2 connections);
  - `inventory-service → inventory-service-postgres` (3 connections).
- **Ztunnel inbound access log, SPIFFE identities:**
  - `spiffe://cluster.local/ns/operations-console-dev/sa/operations-console` → `…/ns/order-service-dev/sa/order-service`;
  - the same source → `…/ns/inventory-service-dev/sa/inventory-service`.
- **Source IP preserved:** Postgres `pg_stat_activity.client_addr` is the service pod IP (`10.128.1.212`, `10.128.1.224`), so pod-selector NetworkPolicies still match.

## L4 graph vs trace for the same order
**Kiali workload graph** (console, order and inventory namespaces, 10 m, security appender):

| Edge | Protocol | mTLS |
|---|---|---|
| operations-console → order-service | tcp | 100% |
| operations-console → inventory-service | tcp | 100% |
| order-service → order-service-postgres | tcp | 100% |
| inventory-service → inventory-service-postgres | tcp | 100% |
| order / inventory / console → `unknown` | tcp | none (Kafka, Keycloak, collector: outside the mesh) |
| `unknown` → order / inventory / console | tcp | none (router, adapter) |

**Tempo trace** `dc1e311f…`: 17 spans across order (3), inventory (6), notification (7) and fulfillment-adapter (1).
- It follows the order: `POST /api/v1/orders`, then the Kafka consumers (`order.placed`, `inventory.reserved`, `fulfillment.requested`, `shipment.confirmed` and others).

**Comparison:**
- The L4 graph shows *who connects to whom, and whether it is encrypted*. It cannot attribute traffic to an order, and the Kafka-mediated business flow appears only as edges to `unknown`.
- The trace shows the *causal path of this order*, including the async Kafka hops, but nothing about transport security.
- **Prediction for the waypoint step:** waypoints add L7 (HTTP) metrics only for the HTTP edges: router → order, console → order and console → inventory. Kafka and Postgres stay L4 (TCP) even with waypoints, so L7 will not show most of the order's path.
