# User-requested change: Place order dropdowns from inventory (2026-11-06)

- **Request:** "The place order screen requires manual text entry. This should be populated with dropdowns by querying the inventory service."
- **Plan:** approved in plan mode. User decisions: customer is a demo-customer dropdown plus "Other"; quantity above available warns but does not block.
- **Implementation:** box1-org/operations-console#5 (`9402793`, branch `run18-place-order-dropdowns`). Front end only.
  - Uses the existing `GET /api/v1/sites`.
  - No backend, contract or other-service change.
- **Live inventory** read anonymously through inventory-service's Route at 2026-11-06 ~00:40 EST: 5 rows.
  - `site_bos` SKU-42 (10);
  - `site_closed` SKU-42 (50);
  - `site_nyc` SKU-42 (100), SKU-7 (25), SKU-LAST (1).

## Results
- `./mvnw clean verify -DskipITs=false`: 50 + 5 tests pass, 0 Checkstyle, 0 SpotBugs (13:4x EST).
- Playwright Firefox, local stack (clocks 13:40:26 / 13:40:26 EST): **18/18 passed**. New tests:
  - dropdowns list inventory sites;
  - the SKU list follows the site (with stock figures);
  - the over-available warning shows while typing and submitting still works;
  - inventory down → named source and typed fallback, and the order is still placed;
  - keyboard-only selection;
  - axe light and dark with 0 violations; no CSP violations.
- First run: 6 failures with **one cause**, a test locator. React Aria renders a Select's label as a `<span>`, not a `<label>`. It was fixed by locating the trigger by accessible name.
- Second run: one **real UX defect**. NumberField commits only on blur, so the warning would appear only as the operator clicked Submit. The warning now follows the typed value.
- **Not yet observed:** the live dropdown check (needs a release after merge and a valid live user).

## Logout fix (box1-gitops#77) status
- Merged 17:58Z. Argo `keycloak` Synced and Healthy (`73d482e`).
- The cluster's KeycloakClient now lists `/callback` and `/signed-out.html`.
- **Live recheck not done:** at 13:41 EST, sign-in as `claude` answered "Invalid username or password" (credential presumably rotated). No further attempts, to avoid lockout.
