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

## Refinement (Phase 6 preparation, 2026-11-06 ~02:25 EST)

The identity is three clients, declared in box1-gitops#78 (approval required):

- `inventory-service`: holds `inventory-admin`; no flows.
- `scenario-controller`: confidential, service account only; tokens carry audience `inventory-service` and `inventory-admin` only. It also declares the caller roles `scenario-viewer` and `scenario-operator`.
- `scenario-controller-cli`: public (PKCE, device grant); tokens carry only audience `scenario-controller` and the assigned `scenario-controller` roles. The controller accepts `azp=scenario-controller-cli` (box1-workloads-dev#103).

The client secret reaches the controller through Secret `scenario-controller-inventory-token`, a user-provisioned new secret. Whether RH-SSO 7.6 enables the device grant by attribute alone is not established.
