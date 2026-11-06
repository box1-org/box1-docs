# D-002: Starfleet Feline Supply is the binding fixture set

- **Status:** decided by the user, 2026-11-06 (prompt, and this run's brief).
- **Decision:** the fixture IDs in `09_scenario_controller.md` are binding: sites `site_spacedock`, `site_ds9`, `site_utopia_planitia`, `site_neutral_zone`; customers `cust_picard`, `cust_data`, `cust_janeway`, `cust_sisko`, `cust_kirk`; the nine `CAT-*` SKUs; assets `asset_replicator_spacedock`, `asset_litterbox_transporter_ds9`. Whimsy stays in names and titles; IDs, errors and audit stay plain. No franchise logos, images or quoted dialogue. Any ID or name change goes to the user.
- **Checked:** every ID matches the contract patterns (`^(cust|site|ord|res|asset)_[A-Za-z0-9_-]+$`; order-service limits `{1,59}`; SKU 1–80 characters).
