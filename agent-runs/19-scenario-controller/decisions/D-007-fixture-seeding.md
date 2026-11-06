# D-007: Fixture seeding through inventory's create-once routes

- **Status:** decided. The user authorized the inventory-service change on 2026-11-06; inventory-service#3 is open, and merging it needs approval.
- **Mechanism:** `PUT /internal/v1/sites/{siteId}` and `PUT /internal/v1/stock/{siteId}/{sku}` (create once; repeat = 200 unchanged; anything else 409). Customers need no seeding (P-7). Telemetry assets are not seeded: `red-alert` is not yet possible (D-009).
- **Fixture stock (opening quantities):**
  - `site_spacedock` (ACTIVE): every `CAT-*` SKU, 500 each.
  - `site_utopia_planitia` (ACTIVE): every `CAT-*` SKU, 2000 each.
  - `site_ds9` (ACTIVE): `CAT-TRIBBLE-TOY` 1; `CAT-COMBADGE-COLLAR`, `CAT-CAPTAINS-BED`, `CAT-DILITHIUM-NIP` 20 each.
  - `site_neutral_zone` (UNAVAILABLE): no stock records. Orders there are rejected `SITE_UNAVAILABLE`.
- **Reset, additive only:** for each fixture site/SKU, if `available` is below its opening quantity, restock the difference with key `stardock-reset-<scenarioRunId>-<site>-<sku>`. Reset never releases reservations, cancels orders or reduces stock. Over many runs `onHand` grows, which is acceptable for demo data.
- **Seeding twice:** the second pass returns 200 for every call, and the state is unchanged.
- **The 409 case is a stop for that call:** if a fixture ID collides with a record that was not created by this seed (for example opened with another quantity), seeding fails with a plain error and changes nothing further.
