# Phase 0 discovery baseline

Observed 2026-11-06 00:47–01:20 EST, read-only. Host and Podman VM clocks agreed (05:50:03 UTC).

## Target repository and deployment

- `box1-org/scenario-controller` (public) exists, created 2026-11-06T05:41Z through the Golden Path (template 1.1.0, onboarding id `b5763557…`). `main` is `203968e`, scaffold only (greeting, info, liveness). PostgreSQL and Kafka were enabled at scaffold time.
- Release pipeline `.tekton/release.yaml` has `security-gates: disabled` (the template default). Earlier runs switched to `gate` and needed the Guava 33.7.2-jre override (run 18 lesson).
- `box1-workloads-dev/workloads/scenario-controller/` (`8af72f9`): deployment, kustomization, namespace, onboarding, postgres, route, service, serviceaccount. Argo Application `scenario-controller` (selfHeal, PruneLast) is Synced and Healthy. Namespace `scenario-controller-dev` has the app pod, a PostgreSQL pod and PVC, a Route `scenario-controller-dev.apps.ocp.box1.org`, and a NetworkPolicy limiting PostgreSQL ingress to the app.
- The pod has `automountServiceAccountToken: false`, so it has no Kubernetes API identity.
- **Database credential:** the template declares the PostgreSQL Secret inline in Git, the pattern tracked in [#41](https://github.com/box1-org/box1-docs/issues/41). Details were reported to the user directly; see decision D-005.

## Platform

- OpenShift `5.0.0-rc.7`; oc client 5.0.0.
- Kafka `box1-kafka` 4.2.0 KRaft, one node pool (`replicas: 1`, controller+broker). Topics: order/inventory/fulfillment/telemetry/notification events, and DLQs for order, inventory, fulfillment, telemetry. Argo Application `box1-kafka` has no automated sync.
- Keycloak (RH-SSO 7.6 operator), realm `box1`, clients `asset-service`, `developer-hub`, `fulfillment-adapter`, `openshell-cli`, `operations-console`, all `ready: true`. No `inventory-service`, `order-service` or `scenario-controller` client.
- ERP VM `legacy-erp` in `legacy-erp-dev`: Running, `runStrategy: Always`, Argo `legacy-erp` with selfHeal; no Service. Its pipeline promoted three times this morning, so another run (#25) appears active there.

## Services the controller would call

| Service | Relevant API | Auth the deployed service accepts | Observed |
|---|---|---|---|
| order-service | `POST /api/v1/orders` (`{customerId, sku, quantity, siteId}`, `Idempotency-Key` required, `X-Consumer-Id` scope, `X-Correlation-Id`), `GET /api/v1/orders?limit&cursor`, `/{id}`, `/{id}/timeline`; no delete or cancel | None (#40) | Two orders from 2026-11-05 still `SUBMITTED` |
| inventory-service | `GET /api/v1/inventory`, `GET /api/v1/reservations/{id}` (read policy `permit`); `POST /internal/v1/stock/{siteId}/{sku}/restock` (add only, 404 if no row), `POST /internal/v1/reservations/{id}/release` | Admin: audience `inventory-service` + role `inventory-admin`; no client exists | Lab seed only, `reserved: 0` everywhere |
| fulfillment-adapter | `GET /api/fulfillments/{id}` (read `permit`); writes and reconcile need `fulfillment-writer` from a public PKCE client (person only) | — | SFTP disabled |
| asset-service | `/api/v1/control/*` (arm → start with confirm token and typed namespace, stop, stop-all, reset, audit); `chaos-operator` role; `X-Box1-Console: 1` on POSTs | `azp=asset-service` only; control paths use the browser-login tenant | Control enabled, chaos disabled, allowlist empty |

Order states: `SUBMITTED`, `RESERVED`, `FULFILLMENT_REQUESTED`, `SHIPPED`, `COMPLETED`, `REJECTED`, `EXCEPTION`, `CANCELLED`. Inventory rejection reasons, in order: `SITE_UNAVAILABLE` (unknown or unavailable site), `UNKNOWN_SKU`, `INSUFFICIENT_STOCK`.

## Consumers of the fixture set

- #18 operator console (deployed) reads `SCENARIO_CONTROLLER_URL` and calls `GET {url}/internal/v1/scenarios` without a token, expecting `[{name, description}]`. It does not start or stop scenarios (its D-010 defers demo control to #19). Its own fixtures are `cust_demo_*` with keys `demo-<scenario>-<date>-<n>` (D-011).

## Other runs active on this machine

- run15 containers `run15-pg` (15432), `run15-kafka` (19092), `run15-keycloak` (18180) are up. #16 is stopped at Phase 6 and likely to resume (`run16-*`). #18 is in Phase 7 (`run18-*`). #25 appears active on the ERP VM. This run uses only `run19-*` names.

Detailed per-scenario evidence: `01-mechanism-classification.md`.
