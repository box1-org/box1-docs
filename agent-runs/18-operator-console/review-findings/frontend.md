# Review pass: Front end and accessibility (fresh subagent, operations-console d007f00)

**Summary from the reviewer:**
- Hiding is cosmetic only; the backend repeats every check.
- The 401 path is correct.
- No external hosts; CSP compatible (no inline script or style; React sets styles through the CSSOM).
- Text contrast ≥ 7:1 in both themes.

The defects are in how state changes are handled.

| ID | Sev | Finding | Outcome |
|---|---|---|---|
| FE-1 | Med | OrderDetail treats EXCEPTION as final and stops polling, although the order is expected to move on after manual reconciliation | **Fixed** |
| FE-2 | Med | Pausing polling, reaching a final state or paging re-runs a foreground load: spinner, lost focus, extra request | **Fixed**: polling separate from loads; lists keep data while paging |
| FE-3 | Med | A failed background refresh replaces data with an alert and flaps. Polling continues after 401/403. An out-of-order response or an un-aborted `reload` can land on the wrong page | **Fixed**: background errors keep data with quiet note; stop on 401/403; sequence + abort |
| FE-4 | Med | Idempotency key: lost when leaving the page after an ambiguous 503 (duplicate risk); editing fields with the same key gives a dead-end 409 (overlaps ARCH-4) | **Fixed** (with ARCH-4); Firefox test retries after a real ambiguous timeout and a page change → one order |
| FE-5 | Med | Delivery shows two forbidden alerts, and "forbidden" on a 401 | **Fixed** |
| FE-6 | Med | Mobile CSS hides `thead` and turns the table into blocks, so cells lose their labels (a11y and sighted users). The mobile screenshot was taken while the page was still loading | **Fixed**: tables keep semantics in a scrollable labelled region; mobile axe scan added |
| FE-7 | Low-Med | Input borders at 1.5–1.6:1, below the WCAG 1.4.11 minimum of 3:1 | **Fixed**: control borders `--ink-2` |
| FE-8 | Low | Title never changes per route; focus goes to `main` rather than `h1`; focus lost after submit | **Mostly fixed**: per-route titles; focus to result after submit. Focus still moves to `main` (not `h1`) on navigation; accepted |
| FE-9 | Low | `role=alert` on static states; no `h1` in the session error; count live region recreated; auto-updating pages lack a pause control (2.2.2); IncidentDetail keeps polling after resolution | **Fixed**: static states not alerts; session error has h1; atomic count region; pause control on Home/Incidents/IncidentDetail; IncidentDetail stops when inactive |
| FE-10 | Low | e2e weaker than its names: vacuous no-claim check, idempotency first submit not through the UI, delivery table / dark mode / mobile not scanned, roles test omits 4 operations, no CSP-violation listener | **Fixed**: vacuous check removed; UI idempotency path; dark/mobile/delivery scans; roles test covers all operations; CSP-violation listener (which then found a real CSP defect, repair 13) |
| FE-11 | Info | Status tones use colour beyond monochrome; SHIPPED tone is "done"; brand link reloads the app | **Partly**: brand link is a router Link. Status colours kept as functional state colours (accepted, noted against the monochrome brief) |

After repairs (operations-console 1d65b2b): full Maven suite 50+5 green; Playwright Firefox 15/15 rerun on the repaired build.
