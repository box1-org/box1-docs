# D-002 REST authentication

**Status:** resolved 2026-11-05: option A chosen and merge approved by the user. [box1-gitops#69](https://github.com/box1-org/box1-gitops/pull/69) was merged as `60cf703`; Argo `keycloak` is Synced/Healthy and KeycloakClient `fulfillment-adapter` is ready=true. Role existence and assignment are admin-console steps for the user (this run does not use admin credentials).

**Gap:** anonymous callers must never create fulfillments through the Route.

**Options:**
- A (recommended) Bearer JWT from realm `box1`, as inventory D-010: issuer `https://keycloak.apps.ocp.box1.org/auth/realms/box1`, audience `fulfillment-adapter`, client role `fulfillment-writer` in `resource_access.fulfillment-adapter.roles`. `POST /api/fulfillments` and `/internal/**` need the role; `GET` follows a read-policy switch (`FULFILLMENT_READ_POLICY`, default `authenticated`, proposed `permit` in dev because status holds IDs and codes only). Needs a new `KeycloakClient` `fulfillment-adapter` with the role, as a `box1-gitops` PR in `platform/identity/keycloak/realm/`. **Approval required.**
- B No Route exposure for the write path. An OpenShift Route cannot filter by method, so this needs a second Service/Route split or removing the Route, which also removes the demo and operator path the user chose REST for.

**Consequences:** The code is fail-closed. Until the client exists, live `POST` returns 401 to anonymous callers and to any token without the audience and role, which already proves the anonymous-rejection criterion; a positive live REST write needs the client.

**Concrete proposal for option A (not opened as a PR; needs approval).** In `box1-gitops` `platform/identity/keycloak/realm/`, add `fulfillment-adapter-client.yaml`, a `keycloak.org/v1alpha1` `KeycloakClient` in the same shape as `openshell-cli`:
- `clientId: fulfillment-adapter`; public client with PKCE and a loopback redirect, so operators get tokens from a CLI. No client secret exists.
- Client role `fulfillment-writer`.
- An `oidc-audience-mapper` that adds audience `fulfillment-adapter`.

Then add it to the realm kustomization. Granting the role to a user or group is a separate realm administration step. The adapter needs no change: it already checks issuer, audience and `resource_access.fulfillment-adapter.roles`. Until then, every live write returns 401.
