# D-008 Threshold policies and hysteresis

**Status:** decided by the agent, Phase 1.

Policy per metric, overridable per site and per asset through configuration (`asset.thresholds.<metric>.*`, `asset.thresholds.site.<siteId>.<metric>.*`, `asset.thresholds.asset.<assetId>.<metric>.*`; most specific wins). Defaults:

| Metric | Unit | Warning | Critical | Clear below | Bounds accepted |
|---|---|---|---|---|---|
| temperature | C (F accepted, converted) | 80 | 95 | 75 | -50 to 250 C |
| vibration | mm/s | 7.1 | 11.2 | 6.0 | 0 to 100 |
| pressure | bar | 8.0 | 10.0 | 7.5 | 0 to 50 |
| power | kW | 400 | 480 | 380 | 0 to 5000 |

- **Debounce:** while inactive, readings at or above warning count toward activation and the alert activates at the 3rd; one reading at or above critical activates immediately. Readings inside the band between the clear level and warning neither count nor reset; a reading below the clear level resets the count. While active, 3 consecutive readings below the clear level clear the alert, and any other reading resets that count. That band is the hysteresis.
- **Why the band does not reset activation:** the first draft reset the count on in-band readings. A value flapping across the warning level then never activated at all, which contradicts the prompt's "flapping near a threshold gives one alert then one clear". Found while designing the test, before any code depended on it.
- **Deduplication:** one alert row per active episode per `(assetId, metricName)`, enforced by a partial unique index on active alerts. Repeated breaching readings update `lastValue`, `peakValue`, `readingCount` and may raise severity WARNING to CRITICAL in place; they never create a second alert or a second event.
- **Events:** `equipment.threshold-exceeded.v1` once per activation, written to the outbox in the same transaction as the alert row. Escalation and clear are recorded on the alert (API `GET /api/v1/alerts`) but not emitted, because only that event exists in the contract. Clear events are a contract follow-up.
- **Ordering:** evaluation is per `(assetId, metricName)` in consumption order, which is per-partition order of the `assetId` key. A reading whose `measuredAt` is older than the last evaluated reading for that pair is stored but not evaluated (counted as `out_of_order`), so out-of-order delivery cannot flip state backwards.
