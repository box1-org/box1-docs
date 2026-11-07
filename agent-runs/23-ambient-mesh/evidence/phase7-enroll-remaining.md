# Enrollment 3: the remaining four namespaces — all seven in ambient L4 (2026-11-06 America/New_York)

**Change:** [box1-workloads-dev#149](https://github.com/box1-org/box1-workloads-dev/pull/149), squash-merged at the user's instruction as `cb603b2` (22:44:00 EST). Argo auto-synced `fulfillment-adapter`, `notification-service`, `asset-service` and `scenario-controller` by 22:44:13.

## Capture
- All eight pods (four services and four Postgres) have `ambient.istio.io/redirection: enabled`, are ready, and have 0 restarts.
- Namespaces with `istio.io/dataplane-mode=ambient`: all seven Box1 service namespaces.

## Disruption at capture (03:44:11–03:44:33Z), all self-recovered

| Service | Observed | Recovery |
|---|---|---|
| fulfillment-adapter | 2 DB connections closed; 1 outbox poll failed; 1 scheduler exchange failed (`SQLState 08006`). The open **SFTP session to the ERP VM was reset**: 1 poll failed with `Cannot change directory to: outbound`, then Camel `force disconnecting … and re-connecting at next poll` | Next poll |
| notification-service | 4 DB connections closed; outbox, delivery and housekeeping polls failed once. At 03:44:33 the existing **Kafka producer connection was reset** (`NETWORK_EXCEPTION`, `Disconnected from node 0`, retrying) | No warnings after 03:44:33 |
| asset-service | 4 DB connections closed; 3 outbox-claim and 1 reaper failures (03:44:12–14) | Self |
| scenario-controller | 1 DB connection closed | Self |

**Nothing was stuck or lost:**
- `fulfillment_needs_attention`, `fulfillment_quarantined_files`, `fulfillment_backlog`, `fulfillment_awaiting_operator`, `fulfillment_oldest_unacknowledged_seconds`, `fulfillment_outbox_pending`, `box1_notification_outbox_pending`, `box1_notification_pending` and `box1_notification_oldest_pending_age_seconds` were all 0, with a 15-minute max of 0.
- The only firing Box1 alert is `Box1OrdersStuck`, for two SUBMITTED orders from 14:11 and 15:56 UTC that predate this run (noted on #22).

## Business flow (through the adapter and the ERP VM over SFTP, VM outside the mesh)
- `ord_ae2ba6ef22664e71beaf8d435c5a56b1` reached SHIPPED in about 9 s (trace `287cbc775c6224385b92409c98d082ea`).
- `ord_aa4c73a6dba446489828002d502dd78b` reached SHIPPED in about 8 s (trace `513a1bf728867d284ea90717ee857688`).
- Both were submitted 10–30 s after capture.

## mTLS (destination-reported `istio_tcp_connections_opened_total`, cumulative)
- `mutual_tls` on every enrolled-to-enrolled edge:
  - console → order (9), console → inventory (9), console → fulfillment-adapter (1);
  - each service → its Postgres: order 2, inventory 3, adapter 2, notification 4, asset 4, scenario-controller 1.
- Inbound from outside the mesh (router, Kafka clients, adapter callers) is `unknown`, as expected.

**Kiali workload graph** across the seven namespaces (10 m): 21 edges. The 8 enrolled-to-enrolled edges are 100% mTLS; the other 13 go to or from `unknown` (Kafka, Keycloak, MailHog, the collector, the ERP VM and the router are outside the mesh).

## Data-plane cost with seven namespaces enrolled
ztunnel 6m CPU and 10Mi; istio-cni 1m and 140Mi; istiod 2m and 168Mi; Kiali 3m and 76Mi. Node: 3,991m (12%) and 87,633Mi (68%). The node's memory moves by ±3 GiB between samples, which is larger than the mesh's cost.
