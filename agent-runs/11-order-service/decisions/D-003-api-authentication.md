# D-003 API authentication boundary

**Status:** resolved 2026-11-05 by the user: option B, no authentication for this pilot. Tracked in box1-docs#40.

**Conflict:**

- `02_REPO_AND_GITOPS_CONVENTIONS.md` says not to expose internal microservices through Routes. `01_DOMAIN_CONTRACTS.md` requires AuthN/AuthZ at backend boundaries.
- The prompt scopes idempotency by "consumer/account", which needs a trustworthy caller identity.
- The `box1-quarkus-smoke` cluster task requires the public Route `https://<namespace>.apps.ocp.box1.org` with unauthenticated `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi` and `/q/metrics`, and asserts `box1_greetings_total`. Removing the Route or those paths fails every release.

**Observed:** the Route resolves to a private LAN address and answered from the workstation without credentials. Internet reachability was not tested. Keycloak is deployed at `keycloak.apps.ocp.box1.org`. Whether its realm suits this service is not established.

**Options:**

- **A (recommended): require a Keycloak bearer token on `/api/v1/**`.** The smoke paths stay open. Idempotency scope comes from a token claim, and internal replay needs a role. A new Keycloak client needs its own approval.
- **B: no authentication for this pilot.** Idempotency scope comes from an untrusted caller-supplied value, and the gap stays recorded as a lab limitation. Order data would be readable on the LAN without credentials, and `ORD-VS-AUTHZ` could not pass.

**Default regardless of option:** keep the scaffold's greeting endpoints and metric so smoke passes, rather than change a shared platform task.
