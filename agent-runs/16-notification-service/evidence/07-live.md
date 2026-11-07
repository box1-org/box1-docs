# Phase 6–7 live evidence

Observed 2026-11-06 18:18–18:25 UTC (13:18–13:25 EST), read-only, apart from the approved actions in `06-delivery-incident.md`.

## Deployment (release check)

| Check | Observed |
|---|---|
| Argo Application `notification-service` | Synced / Healthy at box1-workloads-dev `2c8f93c` |
| Image | Promotion #108 deploys `sha256:69788422d2f3beef94a255e4247ba3142f662f9edb25018489f2058edd5b363a`, built by `notification-service-release-mpbtb` from `bacc353` |
| Running pod | `notification-service-b45bd85b7-l947t`; `imageID` ends in the same digest; 0 restarts |
| Deployment annotation | `box1.org/source-revision: bacc3538a3dfc8e7eace15bcde967897cd3a90c8` |
| `/api/info` | `gitRef` = `bacc353…` |
| PostgreSQL | `notification-service-postgres` Running and Ready |
| Startup log | "Dead-letter topic box1.notification.dlq.v1 exists"<br>"Events floor 2026-11-06T18:03:00Z; provider stub"<br>Flyway validated 1 migration<br>both channels configured, with dead-letter producers |
| Memory | `oc adm top`: 15m CPU, 188Mi, idle after start. Limit 512Mi |
| JVM | PID 1 is `java -Djava.util.logging.manager=… -jar quarkus-run.jar` (read via `oc exec ps` in this service's pod). No launcher script, so `JAVA_TOOL_OPTIONS -XX:MaxRAMPercentage=50` applies |

## Release smoke, run by hand

The pipeline's smoke task never ran, because promote failed earlier. These are the same checks, run through `https://notification-service-dev.apps.ocp.box1.org` with no credentials:

| Request | Result |
|---|---|
| `/api/greetings?name=OpenShift` | `{"message":"Hello from box1, OpenShift!","service":"notification-service"}` |
| `/api/greetings?name=%20` | 400 |
| `/api/info` | name `notification-service`, javaVersion 21, gitRef `bacc353…` |
| `/q/health/live`, `/q/health/ready`, `/q/health/started` | 200 each |
| `/q/openapi` | Paths include `/api/greetings`, `/api/info` and the 5 notification paths |
| `/q/metrics` | Contains `box1_greetings_total`, `box1_notification_pending` and `box1_notification_metrics_snapshot_age_seconds` |

## Negative auth through the Route

| Request | Result |
|---|---|
| `GET /api/v1/notifications?orderId=ord_x`, anonymous | `401`, `WWW-Authenticate: Bearer`, Problem JSON `UNAUTHENTICATED` |
| `POST /api/v1/stub/faults`, anonymous | `401` |
| Same `GET` with a garbage bearer token | `401` |

## Not yet verified live

- That the Keycloak client roles exist. The `notification-service` KeycloakClient is `ready=True`, but its status does not list roles, and no admin credential is issued to the run (#59 check).
- Any path that needs a token (positive read, 403 without the role): needs O-5.
- A real order's shipment or failure producing one notice: needs a reader token to view it.
- Stub 503 run: needs O-4.

## contracts.ref

The pin `1078fd4` is the head of box1-ops-contracts#9. That PR was merged with a merge commit, so the commit is in `main`'s history. No repin is needed. `ContractTest` also passes against contracts `main` `d899bf7`.
