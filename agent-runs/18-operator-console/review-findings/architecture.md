# Review pass: Architecture (fresh subagent, operations-console d007f00)

**Summary from the reviewer:**
- No blockers.
- The console owns no state and reads only published APIs.
- G-1 is isolated in `ConsoleReads.fulfillmentRequestIdFor`.
- D-008 precedence was verified against the adapter source. `ACKNOWLEDGED` implies outcome ≠ AWAITING_ERP, and NEEDS_ATTENTION together with PENDING or HELD happens only for CONFLICTING_REUSE.

| ID | Sev | Finding | Outcome |
|---|---|---|---|
| ARCH-1 | Med | `/overview` returns zeros and "No exceptions" when order-service is down, which guesses values instead of leaving them absent | **Fixed**: indicators null + UI "Indicators unavailable"; test |
| ARCH-2 | Med | `/incidents/{id}/evidence` invents an incident (`ORDER_EXCEPTION`, "resolved") for an order that never had one | **Fixed**: kind `NONE`, "No active incident", no resolution claim; test |
| ARCH-3 | Med | ERP detail is suppressed for EXCEPTION orders and labelled "No ERP request yet", although a request existed | **Fixed**: EXCEPTION included; test |
| ARCH-4 | Med | After a 503 on a timeout where the order did commit, the operator can edit fields, resubmit with the same key, get a permanent 409, and reload into a duplicate. Upstream 401/403/422 also map to 503 "retry is safe" | **Fixed**: 4xx → 502 `UPSTREAM_REFUSED`; UI locks key+values after 503 (sessionStorage), 409 explained; backend test + Firefox UI retry test |
| ARCH-5 | Low-Med | The incident list and `/sites` don't report an incomplete window | **Fixed**: `window` on IncidentList; incomplete stock → DEGRADED |
| ARCH-6 | Low-Med | Incident derivation uses order state only, while D-012 and the UI say "and fulfillment status" | **Fixed (wording)**: D-012/contract/UI say "order status"; adapter-derived incidents not added (next: with #17 or G-1) |
| ARCH-7 | Low | Java Views drift from the YAML: nullable `detail`/`since`/`reasonCode`, quantity 0 used as a guess, null `state` key. The drift test compares only operations | **Partly fixed**: YAML nullability aligned, quantity/stock not guessed, null state skipped, strict duplicate-key check. Not done: schema-validating serialized Views against the YAML (next action) |
| ARCH-8 | Low | Timeline truncation drops the newest entries, but the UI says "older" | **Fixed**: text says newer entries not loaded |
| ARCH-9 | Low | The Link parser can mark an incomplete window as complete (latent) | **Fixed**: param-order-independent Link parsing; unusable next → incomplete; test |
| ARCH-10 | Info | #17 fit: `sources` vs `sourceStatus`, `inc_ord_` id pattern and closed `kind` enum, offset paging over a moving window | **Partly fixed**: id pattern `^inc_…`, `kind` extensible; `sources` name kept (prompt asks for #17's semantics, not its name); offset paging over a moving window recorded in D-013 |

After repairs (operations-console 1d65b2b): full Maven suite 50+5 green; Playwright Firefox 15/15 rerun on the repaired build.
