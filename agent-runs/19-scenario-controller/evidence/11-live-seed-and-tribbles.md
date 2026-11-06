# Live: seeding and The Trouble with Tribbles on the cluster, 2026-11-06 15:41–15:42 EST

The user ran both from the operations console's Demo control page, after the `roles` scope fix (box1-org/box1-gitops#84, `8203a7d`). The results below were read back read-only through the console API as the test user.

| Audit seq | Time (UTC) | Action | Outcome | Actor | Detail |
|---|---|---|---|---|---|
| 11 | 20:41:27 | SEED | OK | the user (subject and username) | `created=26; unchanged=0` |
| 12 | 20:42:08 | START `inventory-contention` | ACCEPTED | the user | ttlSeconds=180; mode=SERVICE_API; targets: the three in-cluster services and Keycloak |
| 13 | 20:42:08 | ORDERS_PLACED | OK | system | two orders, quantity 1 each |
| 14 | 20:42:10 | RESULT | **VERIFIED** | system | One reservation won (`ord_e3eed2ae…`) for the last tribble; `ord_9242bce4…` REJECTED `INSUFFICIENT_STOCK`; site_ds9 CAT-TRIBBLE-TOY available 0 |
| 15 | 20:42:10 | RESET | RESET_OK | system | site_ds9 CAT-TRIBBLE-TOY restored from 0 to 1 |

Run `scn_2bbc06797d066122ba9e`.

**Earlier runs that failed** (`scn_0067ac64…`, `scn_50a8ea34…`, `scn_6ebc8cb3…`): each started before seeding succeeded. Each failed at once with "Fixtures are not seeded" and reset cleanly with nothing to restore. The first seed, at 19:12Z, failed with an inventory 403 (repair 16).

**Issue boxes ticked from this evidence:**
- "The Trouble with Tribbles…" (AC-6).
- "Every scenario shows its display title…" (AC-8): the live catalog and audit through the console.

**Not established live:**
- Seeding twice giving the same state: only the first seed was run live.
- The other scenarios.
- An ERP hold.
- A pod restart mid-run.
