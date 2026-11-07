# D-016 Read policy for the status API in dev

**Status:** decided by the agent in Phase 5, 2026-11-05. The user can reverse it with one environment change.

**Gap:** `GET /api/fulfillments/{id}` defaults to needing a token. With no Keycloak client (D-002), nobody could read status through the Route, including operators and the live acceptance checks.

**Options:** A (chosen) `FULFILLMENT_READ_POLICY=permit` in `fulfillment-adapter-dev` only, as inventory D-011 did. The response holds IDs, SKU, quantity, ERP codes and timestamps; no customer data; never the ERP reason text. B keep `authenticated` until D-002 is approved.

**Consequences:** Writes and `/internal/**` stay role-protected whatever this setting is. Switching to B is a one-line `env` change in the workloads Deployment.
