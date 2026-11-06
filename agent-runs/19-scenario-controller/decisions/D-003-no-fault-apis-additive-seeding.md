# D-003: No fault API in any other service; seed only through each service's own API, additively

- **Status:** decided by the user, 2026-11-06.
- **Decision:** never add a fault API to the ERP or any other service. A scenario the platform cannot support yet is recorded as "not yet possible", not faked. Fixtures are seeded only through each service's own API, and only ever added.
- **Consequence found in Phase 0:** inventory-service has no API that creates a site or a site/SKU stock row (`evidence/01-mechanism-classification.md`, P-1). Seeding the fixture sites therefore needs an inventory-service change, which is outside this run's push authority. Open decision O-2.
