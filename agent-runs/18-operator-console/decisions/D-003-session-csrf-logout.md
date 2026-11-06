# D-003 Session, CSRF and logout

**Status:** decided. The session key needs the user's decision (O-3).

- **One OIDC tenant, `web-app` code flow.** All protected paths use it.
  - The console exposes **no bearer-token API**, so a session cookie can never authenticate a bearer API (the asset-service SEC lesson).
  - `quarkus.http.auth.proactive=false`.
- **Challenge:**
  - Page requests (HTML navigation) get 302 to Keycloak.
  - `/api/*` requests without a valid session get **401** Problem JSON, never a redirect. This needs a small custom `HttpAuthenticationMechanism` that delegates to the OIDC mechanism and overrides the challenge for `/api/`. The prompt requires 401; asset-service's 499 does not meet it.
  - Authenticated users without the needed role get **403** Problem JSON.
- **Cookies:**
  - `q_session*` cookies are HttpOnly, `Secure` (`cookie-force-secure`), `SameSite=Strict` and `Path=/`.
  - `force-redirect-https-scheme=true` because of the edge Route (asset SEC-1).
  - `split-tokens=true`.
  - Tokens are encrypted in the cookie. Page JavaScript never receives a token: `/api/v1/me` returns only a username and roles.
- **CSRF** has three layers:
  1. `SameSite=Strict`.
  2. Every state-changing `/api/*` call must send `X-Box1-Console: 1` and `Content-Type: application/json`. Otherwise it gets 403 `CONSOLE_HEADER_REQUIRED`. A cross-site form cannot set the header, and CORS never allows it.
  3. An `Origin` check: if the header is present it must equal the console's public origin.
- **CORS:** the template allows Developer Hub with `credentials=false`, so no cookie is sent cross-origin. Developer Hub's API tester can still call the public `/api/greetings`. `X-Box1-Console` is **not** in the allowed headers.
- **Logout:** `GET /logout` (OIDC `logout.path`) ends the Keycloak session and clears the cookie, then lands on `/signed-out.html`. Verified by a 401 on `/api/v1/me` after logout.
- **Session key:**
  - The client is public, so there is no client secret to derive the token-encryption key from. Quarkus generates a key per process, and **every restart or rollout signs operators out** (same limit as #63).
  - **Default for this run:** one replica, with the limit recorded and observed.
  - A Secret-backed `token-state-manager.encryption-secret` is a **new secret**, which needs approval. That is user decision O-3.
- **Headers on every page response:**
  - CSP `default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self' https://keycloak.apps.ocp.box1.org; object-src 'none'`
  - XFO DENY, nosniff, `Referrer-Policy: no-referrer`, HSTS.
  - `signed-out.html` uses no inline style. asset-service's version is blocked by its own CSP, so that is not copied.

## Amendment (Phase 5)

- **CSP as implemented:** `form-action 'self'`, without Keycloak. Login is a redirect and logout is a link, so no form posts to Keycloak (SEC-6).
- `style-src` additionally allows exactly one hash, for react-aria-components 1.22.1's `react-aria-pressable-style`. A CSP-violation check in the Firefox e2e found it.
- **Logout is a GET.** Sibling `*.box1.org` pages can trigger sign-out. This is accepted as a nuisance (SEC-4).
- **Public paths are narrowed** to `/q/health*`, `/q/openapi` and `/q/metrics`, plus the template API and the signed-out page (SEC-5).
