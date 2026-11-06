# Live: second seed, Make it so, Hold that order, and Stop, 2026-11-06 15:48–15:52 EST

The user ran all four from the operations console's Demo control page and did the ERP console steps. The results were read back read-only through the console API (audit seq 16–32). Times are UTC.

| Seq | Time | Action | Outcome | Detail |
|---|---|---|---|---|
| 16 | 20:48:35 | SEED (the user) | OK | `created=0; unchanged=26`: the second seed gives the same state |
| 17–21 | 20:50:01–20:50:23 | `baseline-order` (Make it so) | **VERIFIED** | `ord_aeef083b…` placed; operator step "ship `ful_aeef083b…` in the ERP console" done by the user; order reached SHIPPED; the replay returned the same order; RESET_OK, site_spacedock CAT-SPOT-BOWL 499 → 500 |
| 22–27 | 20:50:51–20:51:35 | `erp-manual-hold` (Hold that order, Number One) | **VERIFIED** | Step "hold `ful_20ad4ac7…`" done by the user; HELD_OBSERVED with `fulfillment_held` up from 0.0 and the order still FULFILLMENT_REQUESTED; step "release" done by the user; release verified; RESET_OK, site_utopia_planitia CAT-COMBADGE-COLLAR 1999 → 2000 |
| 28–32 | 20:51:57–20:52:00 | `erp-delayed-processing` (Impulse power only), then STOP by the user | **STOPPED** | STOP ACCEPTED under the user; RESULT STOPPED; RESET_GUIDED restored site_spacedock CAT-PHASER-LASER 499 → 500 and named the console undo step |

**Issue boxes ticked from this evidence and evidence/11:**
- "Fixtures seed idempotently": two seeds (26 created, then 0 created and 26 unchanged), through inventory's create-once routes, which can neither change nor delete.
- "ERP delayed processing or a manual hold reproduces alert and long-running order without data loss; inventory contention shows one reservation":
  - the hold kept the order FULFILLMENT_REQUESTED and was released without loss;
  - the tribble race showed exactly one reservation;
  - **caveat:** no alert rule exists on the platform, so the "alert" is the adapter's `fulfillment_held` gauge rising, as recorded in AC-3's limitations.

**Still open on the cluster:**
- A guided step not performed timing out as NOT_VERIFIED (shown locally only).
- The non-allowlisted namespace (locally only).
- A pod restart mid-run: the user marked it overtaken by events on 2026-11-06; it remains locally tested only.
- The crash scenario: demo faults are off on the cluster ERP.
