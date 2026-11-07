# D-007 Read API, Keycloak client, roles and accepted tokens

**Status:** proposed. **The client, roles and accepted tokens need user approval.**

## Endpoints

- `GET /api/v1/notifications?orderId=` (required; contract pattern `^ord_…`), newest first, at most 100, with each intent's status, attempts, structured failure reason, sources and redacted receipt. Problem JSON (RFC 9457) errors.
- `GET /api/v1/notifications/{notificationId}`.
- `GET /api/v1/stub` — the stub provider's state: provider name, active fault (if any), its expiry, and the fault-control gate. Visible to readers.
- Fault control (D-009): `POST /api/v1/stub/faults`, `DELETE /api/v1/stub/faults`, `GET /api/v1/stub/faults/audit`.
- Golden Path smoke paths stay anonymous: `/api/greetings`, `/api/info`, `/q/*`. Every other path is deny-by-default.

## Keycloak client (box1-gitops PR)

`notification-service`: public client, authorization code + PKCE S256, loopback redirect `http://127.0.0.1/callback` (CLI), `fullScopeAllowed: false`, no direct grants, no service accounts, no secret — the fulfillment-adapter shape. Audience mapper `notification-service`. Client roles:

- `notification-reader` — read notifications and the stub state;
- `notification-fault-operator` — switch stub fault modes. Does not imply reader.

## Accepted tokens

Validation with smallrye-jwt (the inventory/fulfillment stack): issuer `https://keycloak.apps.ocp.box1.org/auth/realms/box1`, realm JWKS, expiry. Then:

| `azp` | Required `aud` | Roles read from | Grants |
|---|---|---|---|
| `notification-service` | `notification-service` | `resource_access.notification-service.roles` | reader, fault-operator as held |
| `operations-console` **(proposed, configurable, off until approved)** | `operations-console` | `resource_access.operations-console.roles` | `console-viewer` or `console-operator` → reader only |
| any other | — | — | no roles → 403 |

Why: #18's D-002 has the console backend forward the signed-in user's token, which carries `azp=operations-console`, its own audience and (with `fullScopeAllowed: false`) only console roles. Accepting that shape lets the console read notices with **no change to the console client or code**. The alternative — a `notification-service` audience mapper and role scope on the console client — is a change to #18's client and is not this run's to make.

`azp` is checked because Keycloak may add a client's audience to another client's token when the user holds that client's roles (asset-service SEC-3). Fault control is never granted to a console token. Roles never come from a top-level `groups` claim.

Config: `NOTIFY_AUTH_CONSOLE_CLIENT_ID` (default empty = not accepted), `NOTIFY_AUTH_CONSOLE_READER_ROLES` (default `console-viewer,console-operator`).

After the client syncs, check the roles exist on the cluster (#59 lesson; #59 closed as not a defect).
