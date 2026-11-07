# Persistence pass

Fresh read-only subagent, given the diffs (asset-service 0dc14dc..3c40e8c, workloads), prompt, domain contracts and profile; not the implementation reasoning. 2026-11-05 ~19:30 EST. Outcomes are recorded in the table at the end after repairs.

PERS-1 (medium) Forward-skewed reading suspends evaluation. Validator admits up to +5 min; alert_state.last_measured_at takes that value; later correctly-timed readings are STORED_NOT_EVALUATED for minutes. Consumer path has no future bound at all (replay or another producer with a far-future measuredAt disables evaluation until that date and escapes age retention). Fix: bound measuredAt on the consumer path and clamp the stored watermark.
PERS-2 (medium) stop-all can miss a run being started: start commits RUNNING before launch() adds it to `active`; stop-all in between clears `active` without it, marks the row STOPPED, then launch schedules ticks and it emits until the next heartbeat (<=5 s), possibly after reset resumed the producer.
PERS-3 (low) Natural-key dedup, not eventId (contract invariant 4). A replay after the latest reading was retained away is re-evaluated because the check is `isBefore`, double-counting streaks. Fix `<=`; document the deviation.
PERS-4 (low) Age retention deletes one 5000-row batch a minute (~83/s) below the 100/s ingest cap; count(*) over up to 2M rows each minute. Fix: loop batches within a time budget; avoid count(*).
PERS-5 (low) asset_last_seen and alert_state never pruned; stale-asset gauge counts long-gone assets forever.
PERS-6 (low) Outbox claim (60 s) can lapse during a 100-row batch with 15 s timeouts; multi-replica double publish; unconditional mark; per-key order lost after a failure.
PERS-7 (low) arm() inserts the run and its ARM audit in separate autocommit statements.
PERS-8 (low) start refusals other than CONFIRM_MISMATCH are not audited (NAMESPACE_MISMATCH, gate, CONCURRENCY_CAP).
PERS-9 (low) Audit guard is not tamper-proof against the owning role (TRUNCATE, DISABLE TRIGGER). Add a TRUNCATE trigger; document the limit; separate owner is box1-docs#41 territory.
PERS-10 (low) PVC has no Prune=false/Delete=false guard; no backup; Secret out of band means recovery needs the runbook step.
PERS-11 (info) V1 forward-only; future migrations must be expand/contract.

Verified OK (reviewer): JTA enlistment of Agroal connections; FOR UPDATE and per-key serial processing; unique constraints; advisory lock makes the concurrency cap safe; database clock for run timing; indexes fit queries; retention locks; database-outage behavior.

## Outcomes (asset-service 7cdc138, workloads bb0bcae)

| Finding | Outcome |
|---|---|
| PERS-1 | Fixed (see ARCH-1). |
| PERS-2 | Fixed (see ARCH-7). |
| PERS-3 | Fixed: `<=` comparison. Natural-key dedup kept and documented; reading eventIds are now derived from the natural key (MSG-4), so both dedup rules agree. |
| PERS-4 | Fixed. Batches loop within a 20 s budget; planner estimate before an exact count. |
| PERS-5 | Fixed (see ARCH-8). |
| PERS-6 | Fixed. 20-row claims; a batch stops at the first failure and backs off the rest. Single replica documented. |
| PERS-7 | Fixed (see ARCH-9). |
| PERS-8 | Fixed. Every start refusal writes a DENIED audit row. |
| PERS-9 | Partly fixed: TRUNCATE trigger added and tested; owner-role limit documented (needs a separate migration owner, #41). |
| PERS-10 | Fixed: PVC `Prune=false,Delete=false`; dump/restore documented (restore not exercised). |
| PERS-11 | Documented (forward-only; future migrations expand/contract). |
