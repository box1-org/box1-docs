# Checkpoint: box1-docs#18 operator console (frontier)

**Current phase:** 7 Live acceptance, stopped. The checks need a signed-in session through the Route.
**Updated:** 2026-11-06 ~00:27 EST.

## Deployed state (`evidence/05-delivery.md`)
- operations-console `main` `267152e` → image `sha256:584e7e37…`. Promotion box1-workloads-dev#96 merged at `b3a1a52`. Argo Synced and Healthy.
- Release `operations-console-release-859h8`: gate, smoke and console-smoke passed.
- Keycloak client `operations-console` ready. Its roles were not checked by the run.
- Live-verified so far:
  - anonymous 401 on every console API path;
  - RH-SSO login for the client with PKCE;
  - security headers;
  - brand mark;
  - delivery and revision consistency.

## Exact next action
Once the user has signed in, or has approved a run test user, work through this checklist on `https://operations-console-dev.apps.ocp.box1.org` in Firefox:

1. Sign in. Navigation matches the roles; Delivery is shown only with `console-developer`.
2. Run `session.spec`, `roles.spec`, `a11y.spec` and partial-source checks with `CONSOLE_URL` pointing at the Route.
   - Tokens absent from JS and storage.
   - Hosts contacted are only the Route and `keycloak.apps.ocp.box1.org`.
3. Logout ends the session (`/api/v1/me` → 401).
4. A user without console roles gets 403 `ROLE_REQUIRED` through the Route.
5. Sites shows inventory stock, with asset-service "refused the console" (G-2).
6. After fixture approval (O-6), place `cust_demo_ada` orders.
   - Follow one to shipped/completed with timeline and evidence links (needs the real pipeline to progress orders).
   - ERP detail shows "unavailable" while `CONSOLE_FULFILLMENT_LINK=none` (O-1).
   - The held stage is blocked by G-3.
7. With approval: a pod restart. Observe sign-out (D-003).

## Open decisions
`open-decisions.md` (O-1…O-9). O-7 is done: the merges happened. Role assignment is with the user.
