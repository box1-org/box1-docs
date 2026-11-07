# Operations pass

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`).

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | Medium | Flyway retries (~28 min, exponential) exceed the 150 s startup probe | **Fixed.** 25 tries, 5 s apart |
| 2 | Medium | Interrupt dead-letters a valid event | **Fixed** (messaging 1) |
| 3 | Medium | Re-notify procedure does not work | **Fixed** in runbook |
| 4 | Medium | `NOTIFY_EVENTS_FLOOR` is the PR time, not the deploy time | **Open:** the user sets it to the merge time when approving box1-workloads-dev#94, or accepts notices for events in between; stated in the runbook and handoff |
| 5 | Medium | Replay commands imprecise and too broad | **Fixed** (broker pod `box1-kafka-box1-kafka-0` verified read-only; replay channel; headers listed) |
| 6 | Low | 512 Mi limit is tight; whether the image's launcher overrides `MaxRAMPercentage` is unknown | **Phase 7:** measure working set and JVM flags on the cluster; no change before evidence |
| 7 | Low | Pending gauges freeze during a DB outage | **Fixed.** `box1_notification_metrics_snapshot_age_seconds`; consumer-lag metric named in the runbook (not verified) |
| 8 | Low | Alerts described but not deployed; lazy counters miss first increase | **Fixed:** runbook says signals, not alerts (#22); failure counters pre-registered at zero |
| 9 | Low | `box1.outbox.*` has no service prefix | **Fixed.** `box1.notification.outbox.*` |
| 10 | Low | Readiness ping has no short timeouts | **Fixed.** Acquisition 1.5 s, connect 2 s |
| 11 | Low | Rollout ordering (Secret, DLQ, Keycloak) | **Already in D-014**; DLQ now also enforced at startup |
| 12–14 | Info | Shutdown, correlation, Secret command | No change; trace export waits on #22 |
