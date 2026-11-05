# RHDH: Keycloak OIDC authentication and user catalog sync

**Date:** 2026-11-05 (America/New_York)
**Status:** Complete.

## Outcome

Developer Hub now authenticates users through Keycloak OIDC instead of GitHub. Users sign in against the `box1` Keycloak realm, and the Keycloak catalog backend module syncs realm users and groups into the RHDH catalog every 30 minutes. The `emailMatchingUserEntityProfileEmail` resolver maps the OIDC token email to the catalog User entity created by the sync.

## Starting baseline

RHDH used GitHub OAuth as the sole sign-in provider (`signInPage: github`). There was no Keycloak client for Developer Hub and no mechanism to bring Keycloak identities into the catalog.

## What changed

| Commit | Change |
|---|---|
| `2195447` | Confidential OIDC `KeycloakClient` for `developer-hub` in the `box1` realm; OIDC provider added to `app-config.yaml`; `signInPage` changed from `github` to `oidc` |
| `ac52264` | `scope` → `additionalScopes` (`scope` is no longer accepted by this RHDH version) |
| `5315530` | `catalog-backend-module-keycloak-dynamic` plugin enabled; `keycloakOrg` catalog provider configured; `serviceAccountsEnabled: true` on the Keycloak client |
| `28ececd` | `serviceAccountClientRoles` added to the `KeycloakClient` YAML to persist `realm-management` → `view-users` and `view-groups` assignments across Keycloak operator reconciles |
| `acd4926` | `prompt: login` added to skip the silent `prompt=none` check that returned `login_required` |
| `cbd10f1` | Keycloak catalog sync schedule restored to production values (PT30M / PT10M / PT15S) after debug run with reduced intervals |

**Files changed in `box1-gitops`:**

- `platform/identity/keycloak/realm/developer-hub-client.yaml` — new `KeycloakClient`
- `platform/identity/keycloak/realm/kustomization.yaml` — includes the new client
- `platform/developer-hub/app-config.yaml` — OIDC provider, `keycloakOrg` catalog provider, `prompt: login`
- `platform/developer-hub/dynamic-plugins.yaml` — `catalog-backend-module-keycloak-dynamic`

## Issues encountered

**`scope` config option rejected.** The RHDH OIDC provider no longer accepts `scope`; the correct key is `additionalScopes`. `openid` is implicit and must not be listed.

**`usernameMatchingUserEntityName` not available for OIDC.** That resolver is only available on social providers (GitHub, GitLab). The OIDC provider supports `emailMatchingUserEntityProfileEmail` and `emailLocalPartMatchingUserEntityName`. Because the GitHub org catalog names entities after GitHub usernames (e.g. `mike4263`) and Keycloak usernames differ (e.g. `mike`), no resolver could bridge the two without catalog sync.

**Keycloak operator reconciliation wiped manual role assignments.** Granting `view-users` and `view-groups` through the Keycloak UI did not persist because the operator reconciles the client on every sync. The fix was to declare `serviceAccountClientRoles` in the `KeycloakClient` manifest so the operator applies the roles itself.

**`login_required` on every sign-in attempt.** Backstage's OIDC provider probes for an existing session with `prompt=none` before redirecting to the login page. With no prior Keycloak session, Keycloak returns `login_required` and the flow aborts. Setting `prompt: login` bypasses the probe.

**Keycloak catalog sync appeared to do nothing.** The task scheduler (v2) tracks the last-run timestamp in the database. After a pod restart the scheduler waits for the cadence from the previous run, not from the current boot — so the 15-second initial delay only applies on first-ever registration. With a 30-minute cadence the next run was not visible during the session. The schedule was temporarily reduced to 30-second intervals to confirm the sync was working, then restored.

## Final operational state

| Item | State |
|---|---|
| Sign-in provider | Keycloak OIDC, `box1` realm, client `developer-hub` |
| Sign-in resolver | `emailMatchingUserEntityProfileEmail` |
| Catalog sync | `KeycloakOrgEntityProvider:default:refresh`, PT30M cadence, PT15S initial delay |
| Keycloak client secret | In `developer-hub-secrets` as `KEYCLOAK_CLIENT_ID` and `KEYCLOAK_CLIENT_SECRET` (populated manually; not Argo-managed) |
| Service account roles | `realm-management` → `view-users`, `view-groups` declared in `developer-hub-client.yaml` |
| GitHub auth provider | Remains configured but not on the sign-in page; GitHub App integration for catalog (`githubOrg`) is unaffected |
