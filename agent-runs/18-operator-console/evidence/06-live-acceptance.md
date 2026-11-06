# Phase 7: live acceptance through the real Route (2026-11-06 ~00:27–00:35 EST)

- **Signed-in user:** Keycloak user `claude`, issued to this run by the user at ~00:26 EST. The password was kept in a mode-600 file in a private (mode 700) scratch directory and is not recorded anywhere. It has the client roles `console-viewer`, `console-operator` and `console-developer`.
- **Browser:** Playwright **Firefox**. Spec `src/test/e2e/live/live.spec.ts` (operations-console#4), read-only: no orders created, nothing changed.
- **Deployed:** source `267152e`, image `sha256:584e7e37…` (`evidence/05`).

| Check | Result |
|---|---|
| Sign-in via RH-SSO 7.6 (code flow + PKCE), deep link restored | **Pass**. `/api/v1/me` → 200, `{"username":"claude","roles":[viewer,operator,developer],"environment":"operations-console-dev"}`. The client roles exist and reach the token. |
| Front end served from the pod | **Pass**. Every `<script>` is `https://operations-console-dev…/assets/…`; the asset returns 200 with `Cache-Control: … immutable`. |
| Hosts the browser contacted | **Pass**. Exactly `operations-console-dev.apps.ocp.box1.org` and `keycloak.apps.ocp.box1.org`. |
| Tokens in page JS or storage | **Pass**. No JWT in `document.cookie`, localStorage, sessionStorage or page HTML. `q_session*` cookies are HttpOnly, Secure and SameSite=Strict. |
| CSP violations or page errors | **Pass**: none on any page |
| axe WCAG 2.0/2.1 A+AA, light and dark | **Pass**: 0 violations on `/`, `/orders`, `/orders/new`, `/incidents`, `/sites`, `/delivery`, `/demo` and one real order's detail. There were no live incidents to open. |
| Keyboard | **Pass**: skip link, then Tab to Orders, Enter, Orders page. Full order and incident traversal is local only, because no live incident exists. |
| 390 px width | **Pass**: no horizontal overflow on 5 pages |
| CSRF through the Route | **Pass**: no header → 403 `CONSOLE_HEADER_REQUIRED`; form body → 403; sibling `*.box1.org` Origin → 403. None reached order-service. |
| **Logout** | **FAIL.** RH-SSO answers "Invalid redirect uri" for `post_logout_redirect_uri=…/signed-out.html`. The console session ends (`/me` → 401), but the **SSO session survives**: a revisit signs straight back in without the login form. RH-SSO 7.6 validates the post-logout URI against the valid redirect URIs, which #73 narrowed to `/callback`. The local Keycloak 26 honoured the separate attribute, so local e2e passed. Fix: box1-gitops#77 (awaiting approval). |

**Real upstreams as the console sees them:**
- overview: order-service OK (2 ms);
- sites: inventory-service OK (3 ms), asset-service NOT_AUTHORIZED (G-2, as designed);
- delivery: all four upstreams answer `/api/info` (order `11360f2a`, inventory `094772ad`, fulfillment `4c985222`, asset `0d717d08`, console `267152e3`);
- scenarios: NOT_CONFIGURED (#19).

**Live data:** the window held 2 orders, both SUBMITTED, which other runs created. One order's summary: state SUBMITTED, ERP "No ERP request yet", 1 timeline entry, order-service OK. No incidents.

**Not done live:**
- 403 for a user without console roles (the only user issued holds all roles);
- the order flow (fixtures not approved, O-6; the 2 existing orders sit at SUBMITTED);
- held ERP (G-3: the adapter still has `FULFILLMENT_SFTP_ENABLED=false`; its main moved only in `.tekton`);
- pod-restart session behaviour (needs approval).
