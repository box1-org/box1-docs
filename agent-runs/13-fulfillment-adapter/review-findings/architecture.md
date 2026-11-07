# Architecture pass

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| A1 | Medium | Dispatch ignored the stored backend; a second backend's rows would have been uploaded as ERP1 | **Fixed.** Uploads are claimed with `WHERE backend = 'legacy-erp1'`. A full backend interface is not built while only one backend exists. |
| A2 | Medium | Legacy ERP1 types used outside the translation layer (result and dispatch services, transport errors) | **Fixed.** Moved to `backend/`. `ArchitectureTest` fails if the modern core (domain, store, messaging, api, acceptance, reconcile, metrics) imports `erp1` or legacy backend types. `camel/` is integration wiring and part of the translation layer. |
| A3 | Low | D-013 names a `fulfillment-event` route that does not exist | **Documented.** D-013 corrected: Kafka enters route 1 through `direct:accept-command`. |

Checked and correct: the service owns all its tables; there are no cross-service reads; REST and Kafka share one acceptance path that commits before the response; no transaction spans an SFTP transfer or a Kafka send; there is no HTTP to the ERP; host-key checking is strict.
