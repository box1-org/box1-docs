# Phase 0 discovery: observed state

Observed 2026-11-05 22:43–22:55 EST (America/New_York). Read-only. Host and Podman VM clocks agreed at 22:49:40 EST.

## Prompt sources

- PR box1-docs#65 (frontier profile for the console prompt) was **merged** at 2026-11-06T03:33:12Z (22:33 EST). The prompt is read from `origin/main` at `5ef99df`.
- Issue #18 has one comment (mockup, 2026-11-06T03:32Z). The mockup is on branch `issue-18-operator-console-mockup` at `a067c14`, with no PR.
- #59 is **closed**: the RH-SSO operator did create `spec.roles`. The prompt's discovery line ("roles were not created by the operator") is out of date. #63 and #40 are still open.

## Repositories (main SHAs)

| Repo | main | Notes |
|---|---|---|
| operations-console | 5023cda | Onboarded 2026-11-06T03:36Z by the user, template 1.1.0, namespace `operations-console-dev`. Golden Path scaffold only. |
| order-service | 8fda087 | Deployed gitRef matches |
| inventory-service | 6b722a3 | Deployed gitRef matches |
| fulfillment-adapter | 97033af | Deployed gitRef matches |
| asset-service | 828065e | Deployed gitRef matches |
| box1-ops-contracts | d57a4ef | |
| box1-ops-erp-simulator | c84c910 | |
| box1-gitops | 5e05888 | |
| box1-workloads-dev | 723e96e | Onboarding #82, promotion #83 |

## Cluster

- OCP 5.0.0-rc.7 (Kubernetes v1.36.5), single node `quark.host.box1.org`, 31.5 CPU and ~125 GiB allocatable. Requests are at 70% CPU and 67% memory, so there is headroom for one small JVM pod.
- `operations-console-dev`: Argo Application `operations-console` is Synced/Healthy and runs `automated: selfHeal: true` with no prune. Deployment has 1 replica (requests 100m/256Mi, limits 1/512Mi), non-root with a read-only root filesystem. Route `operations-console-dev.apps.ocp.box1.org` uses edge TLS with Redirect. Image digest `sha256:00c55736…6ec6b` from `onb-operations-console-5023cda6`.
- Upstream Services (ClusterIP :8080): `order-service.order-service-dev`, `inventory-service.inventory-service-dev`, `fulfillment-adapter.fulfillment-adapter-dev` and `asset-service.asset-service-dev`. The only NetworkPolicies in those namespaces guard Postgres pods, so in-cluster calls from another namespace are not blocked.
- `box1-ci` has no NetworkPolicy, no EgressFirewall and no cluster proxy.

## Build: `box1-quarkus-maven` (box1-ci)

- The `fetch` step (ubi9/python-311) downloads the source zipball, plus Maven 3.9.16 from Maven Central with a platform-pinned SHA-256.
- The `verify-and-publish` step uses `ubi9/openjdk-21@sha256:bd99…` with no Node. It runs `mvn -B -ntp verify -DskipITs=false` with limits 2 CPU / 3 GiB and `MAVEN_OPTS=-Xmx1024m`. Main builds then run `mvn package -DskipTests` with Jib push, so **the front-end build runs twice on release**.
- PaC takes pipeline definitions from `main` (pilot lesson, run 14).
- Release pipeline: build → `box1-security-gates` (template default `security-gates: disabled`) → `box1-gitops-promote` → `box1-quarkus-smoke`.
- Node capability: see `01-frontend-build-probe.md`.

## Upstream APIs and the tokens they accept

| Service | Console needs | Auth on cluster | Accepts a token from a new `operations-console` client? |
|---|---|---|---|
| order-service | create, list, get, timeline | **None** (#40). CORS: Developer Hub only. | No token needed. Calling in-cluster adds no new exposure. |
| inventory-service | reservation by id, stock | smallrye-jwt: issuer box1, `aud=inventory-service`, roles from `resource_access.inventory-service.roles`, **no azp check**. Reads `permit` in dev. | Yes, with an audience mapper on the console client. Reads need no role. |
| fulfillment-adapter | `GET /api/fulfillments/{id}` | smallrye-jwt: `aud=fulfillment-adapter`, **no azp check**. Reads `permit` in dev. Writes need `fulfillment-writer`. | Yes, with an audience mapper. Reads need no role. |
| asset-service | alerts, readings | quarkus-oidc: `aud=asset-service` **and `required-claims.azp=asset-service`** (SEC-3). Reads need `telemetry-reader`. | **No.** A token issued to any other client is refused (401, covered by its tests). Token exchange still issues `azp` = requesting client. **Gap G-2.** |

Anonymous probes (GET only): orders list 200, inventory list 200, fulfillment get-unknown 404 (reads open), asset alerts 401.

## Order → fulfillment link

- order-service derives `fulfillmentRequestId = "ful_" + orderId without "ord_"` (OrderService.java:88-89) and stores it, but **does not expose it** in `Order`, `OrderView` or the timeline.
- The adapter has only `GET /api/fulfillments/{fulfillmentRequestId}`: no lookup by orderId and no list.
- No published API field links an order to its fulfillment. Only an implementation-detail naming convention does. **Gap G-1.**

## Contracts (box1-ops-contracts d57a4ef)

- `ORDER-STATE.md`: states SUBMITTED, RESERVED, FULFILLMENT_REQUESTED, SHIPPED, COMPLETED, REJECTED, EXCEPTION, CANCELLED. The only display label is FULFILLMENT_REQUESTED → "Awaiting ERP acknowledgement".
- `openapi/order-service.yaml` 1.1.0:
  - List takes only `limit` and `cursor` (newest first, Link next). **No filter or sort.**
  - Timeline entries carry `sequence, kind TRANSITION|NOTE, reasonCode, occurredAt, fromState, toState, eventId, eventType, causationId, correlationId, traceId`.
  - Create needs `Idempotency-Key`. `X-Consumer-Id` sets the idempotency scope and is not an identity.
- `openapi/inventory-service.yaml`, `openapi/asset-service.yaml`.
- **No fulfillment-adapter OpenAPI in contracts.** The adapter serves its own: `dispatch` QUEUED|UPLOADED|NEEDS_ATTENTION, `erpAcknowledgement` NONE|ACKNOWLEDGED, `outcome` AWAITING_ERP|PENDING|HELD|SHIPPED|REJECTED, `needsAttentionReason`, `revision`, `uploads`, `resends`, `statusAt`.
- **No incident/evidence contract, no BFF contract, no `sourceStatus` definition** anywhere.

## ERP: can anything hold a request?

- The cluster adapter runs `FULFILLMENT_SFTP_ENABLED=false`, so accepted requests stay QUEUED/AWAITING_ERP. PENDING and HELD cannot occur on the cluster.
- VM `legacy-erp` in `legacy-erp-dev` is Running with no Services. Its VMI restarted at about 22:45 EST, so another run appears active there; this run did not touch it.
- The run 13 local proof of HELD used the run 14 container harness. The ERP console has no HTTP API, and a hold is an operator action.
- **Conclusion:** no ERP on the cluster can hold a request today. **Gap G-3.**

## Keycloak

- RH-SSO 7.6 operator. Realm `box1` lives in `box1-gitops/platform/identity/keycloak/realm/`.
- Clients: `developer-hub`, `openshell-cli`, `asset-service`, `fulfillment-adapter`. All are public PKCE clients with `fullScopeAllowed: false`, an audience mapper, and client roles in `spec.roles`.
- Role assignment to people is a user action in the admin console.

## Brand mark

- asset-service `src/main/resources/META-INF/resources/console/brand/box1-mark.png`: 400×400 RGBA PNG, SHA-256 `11ccbb2dc79258163cc516ed398132ad320ebf9870c75da64cb8b6f2919762ea`.
- It matches the abbreviated hash in asset-service `docs/architecture.md` and is the `box1-org` GitHub avatar supplied by the project owner.
- No favicon has been derived yet. That needs the user's permission (resize only).

## asset-service console login pattern (to reuse)

- A bearer-only default tenant plus a `console` web-app tenant, chosen by path only (`PathTenantResolver`), so that a session cookie never authenticates the API.
- PKCE required. `force-redirect-https-scheme` and `cookie-force-secure` (needed behind the edge Route). `SameSite=Strict`. `java-script-auto-redirect=false` (XHR gets 499). `split-tokens`.
- CSRF: a custom header (`X-Box1-Console: 1`) plus JSON content type on state-changing calls, and CORS without the header.
- CSP `default-src 'self'`, frame-ancestors none, HSTS, `no-store`.
- The session key is generated per process: sign-out on every restart, one replica (#63).
- Tests: `OidcWiremockTestResource` with smallrye-jwt-build tokens. The console had no browser tests and no Node build.
