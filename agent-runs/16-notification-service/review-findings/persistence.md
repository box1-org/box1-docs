# Persistence pass

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`).

No-finding items: unique constraints for fact, receipt and terminal event; concurrent consumers; CHECK constraints; transaction types; indexes for claim and API; migration naming/rerun; audit trigger behaviour.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | FAILED notification can gain a receipt from a late call | **Fixed** (same as architecture 1) |
| M2 | Medium | Batch can outlast its lease; two workers call the provider | **Fixed** (startup bound) |
| L1 | Low | Retention below the topic retention breaks fact dedupe | **Fixed.** `terminal-days` ≥ 15 enforced at startup |
| L2 | Low | A database error recording one attempt stalls the rest of the batch | **Fixed.** Per-intent catch and claim release |
| L3 | Low | Executor rejection at shutdown leaves a claim held | **Fixed.** Propagates to the per-intent catch, which releases |
| L4 | Low | Outbox retention delete has no index | **Fixed.** `ix_outbox_published` |
| I1 | Info | `record` relies on ArC self-interception | **Recorded.** MANDATORY store methods fail loudly if interception is ever lost |
| I2 | Info | `started_at` uses the app clock, `finished_at` DB time | **Recorded**, not changed; no constraint depends on it |
