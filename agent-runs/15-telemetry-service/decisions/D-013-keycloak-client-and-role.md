# D-013 Keycloak client and chaos-operator role

**Status:** OPEN, needs approval (new client and permission). The PR is prepared under standing permission; merge is not approved.

## Proposal

A `KeycloakClient` CR `asset-service` in `box1-gitops/platform/identity/keycloak/realm/`, in the legacy `keycloak.org/v1alpha1` form the realm already uses:

- **Public client, no secret.** Standard (code) flow only, PKCE S256 required, implicit/direct-grant/service accounts off. A public client means no new client secret exists anywhere.
- Redirect URI `https://asset-service-dev.apps.ocp.box1.org/console/*`, web origin the same host. Post-logout redirect to `/console/`.
- Client roles `chaos-operator` and `telemetry-writer`. An audience mapper adds `asset-service` to access tokens.
- Assigning `chaos-operator` to a person is a user action in the Keycloak admin console (the operator does not reliably manage user role mappings; the realm README records the same for realm roles). `telemetry-writer` is assigned to nobody; ingestion through the Route stays closed (D-002).

## What it unlocks, and what stays unproven without it

- With it: positive console login, a live load run and chaos run, live wrong-role 403 (needs a second account or a token before role assignment).
- Without it: live anonymous rejection only. Positive proof stays local, against a Keycloak container configured from the same client definition.
- The live runs must be started by a logged-in person. This run has no credential and will not use one it was not issued. Either the user drives the console for Phase 7, or issues this run a short-lived token by a method they choose.

## Amendment after Phase 5

The proposed client now also defines client role `telemetry-reader` (security review SEC-2). Still public, no secret, and no role assigned by the change.
