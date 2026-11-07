# D-002 Route exposure and access model

**Status:** decided by the agent, Phase 1. Depends on D-013 (Keycloak client) for live positive proof.

## Facts

- The template Route exposes the whole application on `asset-service-dev.apps.ocp.box1.org` (edge TLS, no path).
- The shared `box1-quarkus-smoke` task requires anonymous 200s on `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi` and `/q/metrics` (with `box1_greetings_total`), and 400 for a blank greeting.
- Keycloak is RH-SSO 7.6, issuer `https://keycloak.apps.ocp.box1.org/auth/realms/box1`.

## Options

1. Separate port and Service for ingestion, not routed. Needs a second Quarkus HTTP server (management interface is for `/q`, not business APIs) or a sidecar; changes the template's Service shape.
2. Authentication on every business path, one port. The Golden Path smoke paths stay anonymous because the shared task requires it.

## Decision

Option 2, enforced by the backend with HTTP permissions plus `@RolesAllowed`:

| Path | Access |
|---|---|
| `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi`, `/q/metrics`, `/q/swagger-ui` | anonymous (Golden Path smoke contract) |
| `POST /api/v1/telemetry/readings` | bearer token, client role `telemetry-writer` |
| `GET /api/v1/assets/{assetId}/readings`, `GET /api/v1/alerts` | authenticated (bearer or console session), any role |
| `/console/*` (static page) | authenticated by OIDC code flow, role `chaos-operator` |
| `/api/v1/control/*` | role `chaos-operator`; bearer or console session; state changes need the console's CSRF header |
| anything else | denied |

- One OIDC tenant, `application-type=hybrid`: requests with `Authorization: Bearer` are verified as bearer tokens, browser requests use the authorization code flow with PKCE.
- Roles come only from `resource_access.asset-service.roles` (inventory D-010 lesson: no fallback to a top-level `groups` claim).
- The console session cookie is `HttpOnly`, `Secure`, `SameSite=Strict`. State-changing control calls also require header `X-Box1-Console: 1` with `Content-Type: application/json`, which a cross-site form cannot send without a CORS preflight that the CORS policy refuses.
- CORS stays limited to the Developer Hub origin, as the template set it; control paths are excluded from CORS by the permission check (no credentials, no cookie).
- Ingestion stays closed through the Route until a client is issued the `telemetry-writer` role. No such client is requested by this run: the load generator ingests in-process (D-003). Inside the cluster the same rule applies; there is no anonymous internal port.

## Consequences

- `/q/metrics` and `/q/openapi` remain public, like every Golden Path service today. This is the template's contract, not a choice of this run; changing it needs a smoke-task change outside scope.
- Positive live proof of console login needs D-013. Negative proof (anonymous 401/302, wrong role 403) does not.

## Amendments after Phase 4 and Phase 5

- **Tenant by path only (Phase 4 repair).** `tenant-paths` lost to the session cookie: a console cookie selected the code-flow tenant on the data API. `PathTenantResolver` now decides by path alone.
- **Reads need a role (security review SEC-2).** Any realm user could obtain a token through the public client. Reads now need `telemetry-reader`, `telemetry-writer` or `chaos-operator`.
- **Tokens must be issued to this client (SEC-3).** `required-claims.azp=asset-service` on both tenants, because Keycloak adds `asset-service` to other clients' `aud` when the user holds its roles.
- **Behind the edge (SEC-1).** https redirect URIs, Secure cookies and HSTS; CSP and frame denial on the console (SEC-4).
