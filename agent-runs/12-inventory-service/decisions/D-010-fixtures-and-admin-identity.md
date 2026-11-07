# D-010 Fixtures and restocking identity

**Status:** decided by the agent under the user's delegation: no Keycloak client for now. Operator routes stay closed. Creating a credential on a general delegation was not taken as approved.

- **Seed:** Flyway `V2__seed_lab_fixture.sql`: known sites and stock, reviewable in Git and recorded in `flyway_schema_history`. There is no fixture route.
- **Restock route:** `POST /internal/v1/stock/{siteId}/{sku}/restock` with a required `Idempotency-Key`, positive quantity and a reason. Audited in `stock_movement`, with the subject.
- **Identity:** bearer JWT from the existing Keycloak realm `box1`, verified against its JWKS for signature, expiry, issuer and audience `inventory-service`. The route needs role `inventory-admin` under `resource_access.inventory-service.roles`. No client secret is held by this service, and a JWKS fetch failure rejects the request.
- Enforced in the service, by `@RolesAllowed` on the resource and a check of the client's own claim, because the Route exposes every path and is required by the smoke task. Annotations are used, not path-based HTTP permissions, so they return Problem responses and path forms cannot route around them.

**This is not the #40 exception.** Mutations are authenticated from the first deploy. Until a client exists, every call is rejected and the route is unusable: anonymous 401, wrong role 403.

**Approval needed:** creating a Keycloak client `inventory-service` and role `inventory-admin` is a new credential and permission. Nothing was created. Without it: `INV-ADMIN-RESTOCK` positive proof stays local, with a test-issued key, and live proof covers the rejections only.
