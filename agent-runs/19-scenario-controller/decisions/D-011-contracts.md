# D-011: Contracts (Phase 2)

- **Status:** decided by the agent; the shared-contract change needs the user (no push authority to box1-ops-contracts).
- The controller consumes, and does not copy, the shared contracts: order create body and states (`ORDER-STATE.md`), inventory stock and reservation views (`openapi/inventory-service.yaml`), identifier patterns. Its tests fetch them at a pinned box1-ops-contracts commit, as the other services do.
- The controller's own API is published as its served OpenAPI (`/q/openapi`). It emits no events, so no event schema is added. Whether it belongs in `box1-ops-contracts/openapi/` is a follow-up for when a second consumer (#18) adopts it.
- **Needed shared change:** `openapi/inventory-service.yaml` should list inventory-service#3's two operations. The patch is in `evidence/02-inventory-contract.patch` for the user to apply or approve.
- When the contract change lands and inventory-service bumps its pinned contracts ref, `ContractTest.generatedOpenApiCoversTheContract` must expect 6 operations instead of 4.
