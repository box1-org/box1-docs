# Architecture pass

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`).

No-finding items: state ownership, explicit transitions, no distributed transaction, fact-based dedupe, scope.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | Medium | A provider call that timed out on the final attempt could later write a receipt to a FAILED notification | **Fixed.** Receipt insert locks the notification row and requires a non-terminal status; the worker re-checks for a receipt under the same lock before recording a non-success |
| 2 | Medium | Runbook replay re-produced to topics owned by other services, reaching their consumer groups | **Fixed.** Group-scoped replay channel (`notification-replay`), off by default; runbook forbids re-producing to shared topics |
| 3 | Medium | Fulfillment-sourced notices claimed order outcomes ("needs manual reconciliation", "shipped") the service cannot know | **Fixed.** Wording states what fulfillment reported (template v1 changed before any release) |
| 4 | Low | Notice text depended on which of two events arrived first | **Fixed.** Shared facts render from common fields only; test asserts equal text |
| 5 | Low | Delivery batch could outlive its lease | **Fixed.** Startup requires batch × timeout < lease; default batch 10 |
| 6 | Low | Unknown event types flood the DLQ | **Fixed.** Unknown types acknowledged and counted; known type on the wrong topic stays poison |
| 7 | Low | Recurring identical retryable failures collapse into one notice | **Recorded** as an accepted limitation in docs/architecture.md |
| 8 | Low | DLQ missing from TOPICS.md; DLQ keeps `customerId` of a poisoned `order.placed.v1` for 14 d | **Open decision** O-1 / O-7 for the user |
