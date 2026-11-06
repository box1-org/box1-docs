# D-002 Keycloak client and roles for the console

**Status:** proposed. The GitOps PR needs the user's approval to merge, and **role assignment to people is a user action**.

A `KeycloakClient` `operations-console` in `box1-gitops/platform/identity/keycloak/realm/`, following the realm's existing pattern:

- **Public client, standard flow with PKCE S256.** Implicit flow, direct grants and service accounts are off. `fullScopeAllowed: false`.
  - It is public because a confidential client needs a client secret, which is a new secret. The realm's other clients are all public, and the backend holds the tokens either way. The trade-off: there is no secret to derive a session key from (see D-003).
- **Redirect URI:** `https://operations-console-dev.apps.ocp.box1.org/*`. Web origin is the same host. Post-logout redirect is `/signed-out.html`.
- **Client roles** (on `operations-console`, read from `resource_access.operations-console.roles`):

| Role | Grants |
|---|---|
| `console-viewer` | Read every page: home, orders, order detail, incidents, sites |
| `console-operator` | Viewer, plus place orders (the only write) |
| `console-developer` | Viewer, plus delivery/evidence detail (service revisions) |

  - There is no `admin` role. Demo control does not exist until #19 (D-010), and an unused privileged role is not least privilege. Role names carry a `console-` prefix so they cannot be mistaken for another client's roles.
- **Audience mappers:** `operations-console`, `inventory-service` and `fulfillment-adapter`. These two services accept any box1-realm token with their `aud` and do not check `azp`. Adding the audience is a change to the console's own client, **not** to those services.
  - The console needs no roles from those clients: their reads are role-free, and the console makes no writes to them. So there are no scope mappings for their roles.
- **Not included:** token exchange (a preview feature in RH-SSO 7.6 and a server-level change), a service-account client, and the `asset-service` audience (refused anyway because of `azp`; see gap G-2).
- **After sync:** check that the three roles exist on the cluster (pilot lesson; #59 turned out to be timing). Users receive roles in the admin console.

## Amendment (Phase 5 security review, SEC-1/SEC-2), 2026-11-05 ~23:50 EST

- **Audience mappers for `inventory-service` and `fulfillment-adapter` removed.** The client is public, so any realm user can run a PKCE flow against it and hold its tokens. With those mappers, any realm user, including one with no console role, could have minted tokens for those services. The client now carries only its own audience.
- **The console forwards no user token** (`CONSOLE_FORWARD_USER_TOKEN=false`). The upstreams' reads are open in dev today. When they require tokens, the console needs a client whose tokens are meant for them: user decision O-9. A confidential client would also give a stable session key (O-3).
- **Redirect URI** is exactly `/callback`.
