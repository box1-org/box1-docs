# Phase 6: GitOps delivery (2026-11-06 America/New_York)

Merges were made by the user:
- box1-gitops#73 (`09cd71a`, 00:06:56 EST);
- box1-workloads-dev#90 (`a4e41ea`, 00:09:49);
- operations-console#2 (`a8f2140`, 00:10:30);
- operations-console#3 (`267152e`, ~00:17).

## First release failed at the gate
- `operations-console-release-mtdgc`: build Succeeded (`sha256:6bb693ae…`); `security` **StepFailed**.
  - RHACS: `check exit=1 … 1 policies violated that are failing the check`.
  - The user identified it as CVE-2026-102554 in Guava 33.6.0-jre, which the Quarkus 3.40.1.1 BOM brings in through the OIDC and OpenTelemetry extensions.
  - Nothing was promoted.
- Fix: operations-console#3 overrides Guava to 33.7.2-jre, the same override as asset-service and inventory-service. Locally `dependency:tree` shows 33.7.2-jre, and `clean verify` passes (50+5 tests, 0 Checkstyle, 0 SpotBugs).
  - The PR run `-f2r9j` was **cancelled** by PaC when the PR merged, not failed.

## Second release succeeded
`operations-console-release-859h8` (00:22 EST): build, security (gate), promote, smoke and **console-smoke** all Succeeded.
- image-digest `sha256:584e7e378c18fb838ac30ab8192bc22a8cd08990ce1fcb03d6b6f7bbb09e965f`
- gitops-pr box1-workloads-dev#96, merged at `b3a1a52001a9a83a3dd65c4e66c8a16277ed3167` (05:21:42Z)
- SCAN_OUTPUT `{"critical": 0, "high": 10, "low": 83, "medium": 153}`. The first release had high 11.

## Independent checks (read-only, ~00:24 EST)
- **Argo** `operations-console`: Synced, Healthy, revision `b3a1a52`.
- **Pod** `operations-console-c58b65f86-6ft6c`: Ready, imageID `…@sha256:584e7e37…`.
- **Deployment** annotation `box1.org/source-revision: 267152e…`, which equals `/api/info` `gitRef` `267152e3d1e25d6308cd00d5b1389db2507d55f8`, the merge of PR #3 on main.
- **Route** `https://operations-console-dev.apps.ocp.box1.org`, anonymous:
  - All 9 GET console API paths → **401 `application/problem+json`, no Location**. `POST /api/v1/orders` → 401.
  - `GET /orders` (HTML) → 302 to `https://keycloak.apps.ocp.box1.org/auth/realms/box1/protocol/openid-connect/auth?…client_id=operations-console…`.
  - `/q/swagger-ui/` → 302 (needs a session).
  - `/signed-out.html` → 200 with CSP (including the pressable-style hash), HSTS, `X-Frame-Options: DENY` and `Cache-Control: no-store`.
  - `/brand/box1-mark.png` served from the pod: SHA-256 `11ccbb2d…62ea` (unmodified).
- **console-smoke** also showed RH-SSO 7.6 serving its login page for the client with `redirect_uri=…/callback` and `code_challenge_method=S256`.
- **Keycloak:** `KeycloakClient operations-console` `ready: true`; Argo `keycloak` Synced at `09cd71a`. The client roles were **not checked**: that needs admin credentials not issued to this run.
- **Pod log:** one WARN, the expected per-pod session-key notice. No errors.

## Not yet verified (needs a signed-in session through the Route)
Sign-in, 403 for a user without roles, token absence, logout, pod-restart behaviour, keyboard/axe/mobile on the Route, the hosts contacted, partial pages against the real upstreams, and the order flow.
