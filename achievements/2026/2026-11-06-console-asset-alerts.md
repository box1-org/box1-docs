# Operations console reads asset-service alerts (interim client allowance)

**Date:** 2026-11-06 (America/New_York)
**Status:** Delivered and live-verified for the signed-in read path. This is an **interim mitigation**: [box1-docs#80](https://github.com/box1-org/box1-docs/issues/80) stays open, and the permanent fix is [#79](https://github.com/box1-org/box1-docs/issues/79). An active alert was **not** observed in the console, because none existed and the test-alert attempt was stopped. Alerts on incident evidence are not built.

## Outcome

The operations console's **Sites** page now reads active alerts from asset-service with the signed-in person's own token. It shows them in an "Active equipment alerts" table. When asset-service refuses the read, the page says why instead of showing the old generic "refused the console" message. The person's own asset-service `telemetry-reader` role decides access. Tokens issued to the console can never carry writer or chaos rights into asset-service.

```text
asset-service       box1-ci/asset-service@sha256:6cf93f199f425907ec20a9235167f3d694406d29f5756207c6324dd32f507940       (source c75b6dc)
operations-console  box1-ci/operations-console@sha256:45874d64c799c254070cff01109d259a891ab0b8a27ce562978e9dddbce2c148  (source 43f4d28)
keycloak clients    box1-org/box1-gitops 0403953 (Argo CD app keycloak, Synced/Healthy)
runtime env         box1-org/box1-workloads-dev 0a50497, then 460cb85 (chaos gate)
```

## Starting baseline

- asset-service accepted only tokens issued to its own client (`quarkus.oidc.token.required-claims.azp=asset-service`, security review SEC-3).
- The console's `operations-console` Keycloak client is public, so it carried no asset-service audience. The console sent no token to asset-service.
- Sites showed telemetry as *"refused the console: asset-service accepts only tokens issued to its own client … Use the telemetry console instead."* This was gap G-2 of #18, tracked as #80.
- #80 was blocked on #79, which would make the console client confidential and needs a new secret. The user chose the interim path instead: allow the console's `azp` for reads.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `asset-service` | [#5](https://github.com/box1-org/asset-service/pull/5) | `c75b6dc` | `ClientAccess` (a `SecurityIdentityAugmentor`) replaces the bearer tenant's `azp` required claim. `azp=asset-service` keeps all roles. `azp` in `asset.read-clients` (`ASSET_READ_CLIENTS`, default `operations-console`) keeps **only** `telemetry-reader`. Any other `azp`, or none, gets 401. The console (web-app) tenant keeps `azp=asset-service`. |
| `operations-console` | [#9](https://github.com/box1-org/operations-console/pull/9) | `43f4d28` | `AssetToken` sends the session token to asset-service only, behind `CONSOLE_ASSET_FORWARD_TOKEN` (default false). The same pattern is used for the scenario controller. `/api/v1/sites` gains `alerts`: active alerts, newest first, at most 100, never invented when asset-service fails. Refusal messages distinguish no token, 403 (no reader role) and other 401s. Only the tokenless refusal is cached, so one person's answer never reaches another. |
| `box1-gitops` | [#85](https://github.com/box1-org/box1-gitops/pull/85) | `0403953` | `asset-service` client: internal ID pinned (`0b509c04-6761-4cc3-af7d-be7ac1c7c743`, read from the live KeycloakClient). `operations-console` client: `asset-service` audience mapper, plus a scope mapping for `telemetry-reader` only (`fullScopeAllowed` stays false). README updated with rollback. |
| `box1-workloads-dev` | [#130](https://github.com/box1-org/box1-workloads-dev/pull/130) | `0a50497` | `CONSOLE_ASSET_FORWARD_TOKEN=true`. `ASSET_READ_CLIENTS=operations-console` is set explicitly, so the rollback is one value. |
| `box1-workloads-dev` | [#131](https://github.com/box1-org/box1-workloads-dev/pull/131), [#132](https://github.com/box1-org/box1-workloads-dev/pull/132) | auto | Pipeline promotions of the two images above |
| `box1-workloads-dev` | [#137](https://github.com/box1-org/box1-workloads-dev/pull/137) | `460cb85` | Chaos gate opened in `asset-service-dev` (`ASSET_CHAOS_ENABLED=true`, allowlist `asset-service-dev`). **User decision, 2026-11-06, under #15 D-015: leave it on.** |

**Tradeoff:** the console client is still public, so any realm user can obtain its token directly. That token carries only the `telemetry-reader` role the person already holds, and asset-service drops every other role for this client. It therefore grants nothing new. The confidential client in #79 remains the permanent fix.

## Validation and evidence

Local builds:
- asset-service `./mvnw test`: 48 tests, all passing. New `SecurityTest` cases:
  - console token with reader role: alerts and readings 200, ingestion 403;
  - console token with writer and chaos roles: reads 403, ingestion 403, control refused;
  - `openshell-cli`, `developer-hub` or missing `azp`: 401.
- operations-console `./mvnw verify`: frontend typecheck and build passed; 64 tests, all passing. New `AssetAlertsTest` cases:
  - alerts shown, with the token sent to asset-service only (none to inventory);
  - 403 gives the role message and no alerts;
  - a refusal is not cached for the next person.

Live checks, about 16:30–16:40 EST:

| Check | Expected | Observed |
|---|---|---|
| Deployed revisions | Promoted digests | `/api/info`: asset-service `c75b6dc…`, console `43f4d28…`; pod digests match #131/#132. Argo CD `asset-service`, `operations-console`, `keycloak`: Synced/Healthy. |
| Keycloak mapping applied | Scope mapping created | Operator log: `SUCCESS create client client scope mappings keycloak/operations-console => asset-service` (21:22:30Z) |
| Anonymous `GET /api/v1/alerts` | 401 | 401 |
| Console Sites as `mike` **without** `telemetry-reader` | Accepted client, refused role | asset-service **403** (was 401 before the change). Sites shows "Your account does not hold asset-service's telemetry-reader role …". Stock still loads. |
| Same user after `telemetry-reader` was assigned and they signed in again | asset-service OK | `/api/v1/sites` asset-service source `OK`, `alerts: []`; page shows "No active alerts." |
| Database cross-check | Empty list is correct | `alert` table empty (no alert has ever fired); `reading` 8,827 rows, newest current |

**Not verified:**
- A non-empty alert list on Sites: only the unit tests cover it.
- Live refusal of another client's token: only the unit tests cover it.
- Test alert: a chaos seed (`c0ffee4000000000`, 1 site × 2 assets, temperature, 30 s) was previewed. It would produce a single SPIKE of 121.5 °C. The user stopped the work before anything was armed, so nothing was sent.

**Learned:** a newly assigned Keycloak role reaches the console only after signing out and back in. The first reload after assignment still returned 403.

## Final operational state

- **asset-service** (Argo CD, `box1-workloads-dev`): accepts `operations-console` tokens with `telemetry-reader` only.
- **Chaos gate:** open in `asset-service-dev`, and intended to stay open. Each run still needs `chaos-operator`, arm-then-confirm and the typed namespace.
- **operations-console** (Argo CD): forwards the person's token to asset-service and scenario-controller only. Other upstreams still get no user token.
- **Keycloak** (Argo CD `keycloak`, `box1-gitops`): the console client has the `asset-service` audience and the `telemetry-reader` scope mapping.
- **Role assignment:** `mike` now holds asset-service `telemetry-reader`, assigned by the user in the Keycloak admin console. The assignment is not in Git.

## Recovery and follow-ups

- **Turn off console reads:** set `CONSOLE_ASSET_FORWARD_TOKEN` to `"false"` in `workloads/operations-console/deployment.yaml`.
- **Refuse the console entirely:** set `ASSET_READ_CLIENTS` to `""`. To remove the Keycloak side, delete the `asset-service-audience` mapper and the `asset-service` scope mapping from `platform/identity/keycloak/realm/operations-console-client.yaml`.
- **Close the chaos gate:** set `ASSET_CHAOS_ENABLED` to `'false'` and the allowlist to `''`.
- None of these rollbacks were exercised.

Follow-ups:
- [#80](https://github.com/box1-org/box1-docs/issues/80) open:
  - observe a real active alert on Sites;
  - add alerts to incident evidence.
- [#79](https://github.com/box1-org/box1-docs/issues/79): confidential console client, the permanent fix. Revisit the asset-service mapping then.
- [#63](https://github.com/box1-org/box1-docs/issues/63): restarting asset-service ends asset telemetry console sessions. This was seen again when the chaos-gate rollout restarted the pod.
- **Unfinished, not published:** the order Evidence "Trace" link to the new OpenShift distributed-tracing view (Tempo `box1-observability/box1`, tenant `dev`).
  - A local edit exists on branch `trace-link` of operations-console, in this workstation's `run23-operations-console` worktree. It is uncommitted.
  - It makes the trace link a configurable `console.trace-url-template` (`CONSOLE_TRACE_URL_TEMPLATE`).
  - Its tests were not completed, and the link target was not opened, because it needs OpenShift sign-in.
  - It is not tracked in an issue yet.
