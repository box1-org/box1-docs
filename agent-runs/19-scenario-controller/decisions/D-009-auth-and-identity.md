# D-009: Authorization and outbound identity

- **Status:** inbound decided by the agent; the Keycloak client, roles and any secret need approval (O-3, still open).
- **Inbound:** bearer JWT from realm `box1`, audience `scenario-controller`, roles from `resource_access.scenario-controller.roles` only: `scenario-viewer` (catalog, runs, audit) and `scenario-operator` (also start, stop, reset, seed). Every `/internal/**` path needs one of them, including the catalog read the prompt lists. Smoke paths (`/api/greetings`, `/api/info`, `/q/*`) stay anonymous.
- **#18 console:** it reads the catalog without a token today, so it will get 401 and show the controller as unavailable. Adoption (forwarding a token with this audience) is #18's work and an audience change that needs approval.
- **Outbound:**
  - order-service: no auth (#40);
  - inventory reads and adapter reads: `permit`;
  - inventory admin (seed, reset): a client-credentials token from a confidential `scenario-controller` client carrying audience `inventory-service` and role `inventory-admin`. Needs an `inventory-service` client (#12) and approval.
- **Without the identity:** the controller starts, its gates and audit work, and seeding or reset report "Inventory admin identity is not configured" (`RESET_FAILED`). Nothing degrades silently.
- **Not used:** asset-service control (`red-alert`, not yet possible, P-5); fulfillment writes.
