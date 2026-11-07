# D-003 Protocol location

**Decision:** `box1-ops-contracts/legacy/erp-file/v1/` — `SPEC.md`, `fixtures/` (inbound, outbound and mapping files plus `manifest.json`) and a small Node reference parser used only to check that the fixtures agree with the manifest. The ERP and the adapter each implement the spec and test against the same fixtures; neither copies them (they pin a contracts commit).

**Why a reference parser in contracts:** the repo's convention is that `npm test`/`npm run validate` prove fixtures match the contract. A second, independent implementation of the spec catches ambiguity before two services diverge.
