# Phase 2: contracts

- **Console backend contract:** `operations-console/src/main/resources/META-INF/openapi.yaml` 1.0.0 (branch `issue-18-console`).
  - 10 operations under `/api/v1`, using #17's paths where #17 defines them (D-006).
  - Problem JSON with a stable `code`.
  - `SourceStatus`/`sources` schema, which #17 names but no contract defined before this run.
- **Drift and coverage:**
  - `ContractDriftTest` asserts that the JAX-RS operations equal the contract's operations.
  - `ConsoleSecurityTest` walks every contract operation for anonymous 401 and no-role 403.
  - The front end generates its only API client from the same file (`openapi-typescript`, then `openapi-fetch`).
- **Consumed contracts:**
  - `box1-ops-contracts@d57a4ef`: `ORDER-STATE.md` (state labels; FULFILLMENT_REQUESTED → "Awaiting ERP acknowledgement") and `openapi/order-service.yaml` / `inventory-service.yaml` / `asset-service.yaml`.
  - The fulfillment adapter's served OpenAPI (it has no contract in box1-ops-contracts).
  - Upstream payloads are read with `ignoreUnknown`, so additive upstream changes are harmless.
- **No change to another service's contract.** No local copy of a shared schema: the console's records hold only the fields it reads.
- **Contract re-check at 23:28 EST:** order/inventory/asset main moved, but only `.tekton/release.yaml` changed (scan output). No API change.
