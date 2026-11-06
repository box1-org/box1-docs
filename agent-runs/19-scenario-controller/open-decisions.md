# Open decisions, run 19 (stop 3, Phase 6 after delivery)

Stop 2 reported 2026-11-06 02:30 EST; answered about 12:50 EST. Stop 3 reported about 13:10 EST. Stop 1's decisions (O-1 to O-12) are resolved except O-3 and O-11, which reappear below.

**Resolved at stop 1 (user, 2026-11-06):**
- O-1: the mechanism table is accepted (D-004).
- O-2: the inventory-service change was authorized; it is inventory-service#3.
- O-10: the allowlist was delegated; it is `scenario-controller-dev` (D-006).
- O-12: the Kafka issue was filed as #71.
- O-4 to O-9: per the accepted table, those scenarios are recorded as not yet possible (D-010).

## Needed for delivery (Phase 6), in order

Each item is a separate approval. A-1 to A-6 were approved at stop 2.

**New at stop 3:** A-4b, merge **box1-org/box1-gitops#79** and sync Argo `keycloak` (the scope-mapping fix; needed before seeding and before the CLI client works). A-2b: merge box1-ops-contracts#10.

| ID | Action | What it does | Status |
|---|---|---|---|
| A-1 | Merge **box1-org/inventory-service#3** | Merged by the user (`ad472e1`), released and deployed (evidence/08) | **Done** |
| A-2 | Contract patch to box1-ops-contracts | Authorized; opened **box1-ops-contracts#10** (validate and 76/76 tests pass) | **PR open; merge needs approval** |
| A-3 | Merge **box1-org/scenario-controller#1** | Merged (`f64dee6`); release Succeeded; deployed `sha256:a811c457…` | **Done** |
| A-4 | Merge **box1-org/box1-gitops#78**, Argo sync | Merged (`7d7e0b1`), synced; roles created; scope mappings fail with 404 (repair 14) | **Done, incomplete: needs #79** |
| A-5 | New Secret `scenario-controller-inventory-token` | Created by pipe, value never shown | **Done** |
| A-6 | Merge **box1-org/box1-workloads-dev#103** | Merged (`e28c020`); Argo Synced and Healthy; Recreate | **Done** |
| A-7 | Assign `scenario-operator` (client scenario-controller) to the person who runs scenarios, and get a token from `scenario-controller-cli` | Needed to call the controller. Whether RH-SSO 7.6 enables the device grant by attribute is not established | After A-4 |
| A-8 | **Cluster seeding** | `POST /internal/v1/fixtures/seed`: four sites and 22 stock records through inventory's API; nothing else changes | After A-4b (#79), A-7 |
| A-9 | **Live run: The Trouble with Tribbles** | Two fixture orders; one reserved, one rejected; additive reset | After A-8 |
| A-10 | **Live run: Make it so** | One fixture order; you ship it in the ERP console when the run shows the step (or switch the ERP to AUTO) | After A-8 |
| A-11 | **Live run: Hold that order, Number One** (the guided ERP scenario) | One fixture order; you hold and then release it in the ERP console (`virtctl console legacy-erp -n legacy-erp-dev`). It needs no demo faults. If you don't do the step, it times out as not verified | After A-8 |

## Decisions

| ID | Decision | Recommendation |
|---|---|---|
| O-11 | The controller's database credential while #41 is open: the template Secret is inline in Git in a public repository (details sent to you directly) | Treat the audit store as disposable lab data, as order-service does, until #41; or create a Secret out of band |
| O-13 | **Done:** filed as box1-docs#72 (one ticket, three items). Was: file backlog issues for the follow-ups: (a) an ERP-side expiry for demo faults and holds (ARCH-4, the ERP repo's change); (b) a fixture-only inventory role narrower than `inventory-admin` (SEC-4); (c) rate-limiting audited refusals (SEC-8) | File (a) and (b); (c) can wait |
| O-14 | #18 console adoption: the catalog read now needs a token (prompt: catalog behind operator authorization), so the deployed console's tokenless catalog read gets 401 and shows the controller as unavailable | #18's change (forward a token with audience `scenario-controller`); an audience change needs your approval |
