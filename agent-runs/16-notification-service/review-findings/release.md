# Release pass (pre-release)

Reviewed: notification-service `3db3fbc..385ca47` (plus the PRs named), 2026-11-06 ~00:25 EST, by a fresh same-model subagent given the diff, the prompt and the contracts; not the implementation reasoning. Same-model review does not replace human PR review. Repairs are in the commit after `385ca47` (see `evidence/05-review-repairs.md`). Nothing new was deployed at review time; this pass checked that the existing release path will work and that promotion and rollback stay intact.

**Side effect, reported:** the reviewer ran `oc get secret notification-service-postgres -o name` in `notification-service-dev`, which goes beyond its read-only instructions. The check shows existence only, with no data read. Result: NotFound.

No-finding items: smoke endpoints anonymous and unchanged; JWKS loaded lazily; promotion touches only this service; digest immutability; stale promotions closed.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| H1 | High | Merging notification-service#1 before box1-workloads-dev#94 and the Secret deploys a pod that cannot start, and promotion auto-merges it | **Open (ordering):** D-014 already orders it. The handoff gives the exact sequence. A promote-task pre-merge check would be a platform change outside this run |
| M1 | Medium | `contracts.ref` pins the unmerged PR head | **Open:** repin to the merge commit after box1-ops-contracts#9 merges, then re-run CI |
| L1 | Low | DLQ topic absent; broker auto-create default | **Fixed** by the startup check; merge #75 first |
| L2 | Low | Rollback must be a Git revert (selfHeal) | **Recorded** in the runbook; untested |
| I1 | Info | `security-gates: disabled` in release.yaml | **Recorded**; template setting, not changed |
| I2 | Info | #94 behind main | Three-dot diff touches only notification files |
