# Run #19 persistence review (read-only)

Scope: `run19-scenario-controller` `203968e..e061f6d` (branch `run19-controller`), `run19-inventory-service` `094772a..fca04be` (branch `run19-fixture-admin`). Requirements: `09_scenario_controller.md`, D-008. Static reading only; nothing executed.

## Findings

### PERS-1 (Medium): run ending, RESULT audit and reset are not atomic and not recoverable
- **Where:** `Engine.java:284-298` (`finish`), `Engine.java:198-209` (`recover` only selects `ended_at IS NULL`), `RunStore.java:85-93`.
- **Failure:** `finish` commits `end()` (sets `ended_at`), then writes the RESULT audit, then calls inventory (`restore`, several HTTP calls with a 5 s timeout each), then `resetResult`, then the RESET audit. Each statement autocommits. Two cases:
  1. The pod is killed (rollout, OOM, node drain) after `end()` and before `resetResult`. The run is now ended, so neither `recover()` nor `sweep()` will pick it up again. Fixture stock is not restored, `reset_result` stays NULL forever, and the RESULT and/or RESET audit rows may be missing. That breaks "audit record complete for every run" and "automatic reset if the process crashes mid-scenario".
  2. A DB error on the RESULT audit insert (line 289) throws `StoreException` after `end()` committed. `restore` is skipped. On the worker thread, the exception goes into an unread `Future` (`worker.submit`, line 124), so nothing is logged, and `active = null` (line 252) is skipped.
- **Fix:** Put `end()` and the RESULT audit in one transaction (`@Transactional` method or one connection with `setAutoCommit(false)`). Make the reset re-drivable: have `sweep()`/`recover()` also select `ended_at IS NOT NULL AND reset_result IS NULL` and run `restore` again. The reset key is already per run, so retries are idempotent. Wrap the worker body in try/catch-log, and clear `active` in a `finally`.

### PERS-2 (Medium-Low): a start that fails after insert leaves an orphan open run with no START audit
- **Where:** `Engine.java:111-123`.
- **Failure:** `insert` commits the run. If `audit(START)` or `impact` then fails, the client gets a 5xx. The run row stays open with no START audit row, no handle and no thread. Because of `ux_scenario_run_one_open`, every later start returns 409 until `expires_at + 30 s`, when the sweep expires it. `recover()` will not handle it, because it only runs at startup.
- **Fix:** Insert the run, the START audit and the initial impact in one transaction. Or catch the failure and `end(runId, FAILED, ...)` before rethrowing.

### PERS-3 (Medium-Low): the retention period is configurable but the trigger floor is hard-coded, and the clocks differ
- **Where:** `application.properties:46` (`SCENARIO_AUDIT_RETENTION`, default P90D), `Engine.java:212-215`, `RunStore.java:150-151`, `V1__scenario_schema.sql:43-50`.
- **Failure:**
  - If `SCENARIO_AUDIT_RETENTION` is set below P90D, the cutoff passed to `DELETE ... WHERE occurred_at < ?` includes rows the trigger refuses. The whole statement aborts every day, so nothing is ever purged. The failure only shows up in a scheduler error log.
  - Even at P90D, the cutoff uses the pod clock (`clock.instant()`) while the trigger uses the DB's `now()`. If the pod is ahead of the DB by δ, any row with `occurred_at` in `[db_now-90d, pod_now-90d)` aborts that day's purge. That is a small window, but it fails the whole day.
  - No audit is lost in either case; the failure is retention not running.
- **Fix:** Compute the cutoff in SQL (`now() - ?::interval`). Validate `retention >= P90D` at startup, or drop the property. Better still, implement D-008 as written (see PERS-4).

### PERS-4 (Low): the delete path does not match D-008, and append-only is not enforced against the app's own role
- **Where:** `V1__scenario_schema.sql:42-52`, D-008 ("deletes older rows through a SQL function that is the only permitted delete path"), and `AbandonedRunTest.java:88-90`, which shows an ad-hoc `DELETE` succeeding.
- **Failure:** Any session with DELETE privilege can delete any row older than 90 days, selectively and outside the retention job. The rows are also deletable because `occurred_at` is client-supplied: a backdated insert is immediately deletable. The migrating role (likely the same credential, per D-005/#41) owns the table, so it can `ALTER TABLE ... DISABLE TRIGGER`. For a lab, the trigger is a reasonable guard against accidents, but the decision record over-claims.
- **Fix:** Either correct D-008 to "BEFORE DELETE trigger permits only rows older than 90 days", or add a `SECURITY DEFINER` retention function owned by a separate role and revoke DELETE from the app role. Optionally use `DEFAULT now()` / a CHECK `occurred_at <= now() + interval '1 minute'` to stop backdating. Record the remaining gap under #41.

### PERS-5 (Medium-Low): single-writer assumption is in memory only; a rolling update can abort a live run
- **Where:** `Engine.java:63, 193-209` (`active` is per-JVM; `onStart → recover()` aborts any open run not owned by this JVM).
- **Failure:** D-008 says "one replica". A default `RollingUpdate` Deployment still briefly runs two pods. The new pod's `recover()` sees the old pod's open run, marks it `ABORTED_RESTART` and restores fixtures, while the old pod's thread keeps placing orders until SIGTERM and the 10 s `awaitIdle`. The DB side is safe: first ending wins (`end ... WHERE ended_at IS NULL`). The risk is fixture state touched after reset. A replica count of 2 would make this continuous.
- **Fix:** Use `strategy: Recreate` in the GitOps manifest (not in this repo; verify there). Or hold a Postgres advisory lock / lease row for the controller and take it before `recover()`.

### PERS-6 (Low; fail-closed): fixture reset ratchets `on_hand` upward
- **Where:** `FixtureService.java:54-73`, `InventoryContention.java:31-38`.
- **Failure:** `restore` restocks by `opening - available`. The contention winner's reservation is still ACTIVE at reset time, so `site_ds9/CAT-TRIBBLE-TOY` goes to on_hand 2, reserved 1. If that reservation later expires or is released instead of being consumed by a shipment (ERP down or held, adapter backlog), available becomes 2. Restock cannot reduce stock (D-003), so every later "Trouble with Tribbles" run fails with "Expected exactly 1 ... found 2" until someone fixes inventory by hand. The scenario fails closed, so there is no false success, but the fixture set is not "repeatable".
- **Fix:** Document this as a known limitation and runbook step. Alternatively, have reset wait for or account for held reservations (restore against `on_hand` minus reservations that will be consumed). Or accept "available ≥ 1" and place `available + 1` orders. This needs a design call; it is out of scope for an inventory change.

### PERS-7 (Info): retention SQL has no test
- `RunStore.purge` (both deletes, including the run delete that is guarded by FK and NOT EXISTS) is not exercised by any test. Only a raw `DELETE` of a 91-day row is (`AbandonedRunTest.java:88-90`). Add one test that seeds an old ended run with old audit rows, calls `purge`, and asserts both are gone. A second case should keep a run whose newest audit row is inside the window.

### PERS-8 (Info): audit rows can be written after RESULT
- `Engine.note` (`Engine.java:339-343`) has no `ended_at` guard. If the run thread outlives `halt`'s 10 s `awaitIdle`, it can append `ORDERS_PLACED` or similar rows after RESULT/RESET. This is harmless to integrity (still append-only, ordered by `seq`), but a reader may misread the timeline. `impact` (`RunStore.java:96-100`) is also unguarded, which is fine. Optional: reject notes for ended runs, or record them with outcome `LATE`.

## Checked, no findings

- **One-open-run partial unique index** (`V1:24`, `ON ((true)) WHERE ended_at IS NULL`): correct idiom. At most one row with `ended_at IS NULL`. A concurrent second `insert` gets 23505 → `false` → audited DENIED/409 (`RunStore.java:70-73`, `Engine.java:111-115`). A 23505 from a PK collision is theoretically possible (80-bit random) but negligible. `open()` can use this partial index.
- **Autocommit / Narayana + Agroal (controller):** there is no `@Transactional` anywhere in the controller (grep). Outside a JTA transaction, Agroal hands out connections with `autoCommit=true`, so each `RunStore` statement commits on its own, as the class comment says. That is not a bug in itself; the consequences are PERS-1 and PERS-2.
- **First ending wins:** `end ... WHERE ended_at IS NULL` plus the `synchronized finish` give exactly one terminal state when the thread, stop, sweep and recover race. `progress` is guarded by `ended_at IS NULL`.
- **jsonb impact merge** (`RunStore.java:96-100`): `impact || ?::jsonb` is a single-statement, row-locked, top-level key merge. Concurrent merges serialise and nothing is lost. A key is replaced, not deep-merged, which suits the `fixtures`/`orders` fields. The default `'{}'` avoids `NULL || x`.
- **Retention run delete vs FK/triggers** (`RunStore.java:152-153`): the audit FK is `NO ACTION`. The run delete only targets runs with `NOT EXISTS` audit rows, so no FK violation occurs, and the audit guard trigger is not involved. Open runs (`ended_at IS NULL`) are never deleted. A run whose later audit rows fall inside the window is kept and deleted on a later day. The two deletes are not atomic, but a failure between them only defers run deletion by a day. Running concurrently on two pods is safe (idempotent deletes).
- **Append-only:** UPDATE always raises (falls through to RAISE). DELETE only works for rows older than 90 days by DB time. TRUNCATE, including cascade from `scenario_run`, is blocked.
- **Indexes for queries used:** `find` → PK; `open` → partial unique index; `recent` → `ix_scenario_run_started`; `auditFor` → `ix_scenario_audit_run (run_id, seq)`, which also serves FK checks and the purge NOT EXISTS; `auditPage` → PK `seq`; purge audit delete → `ix_scenario_audit_time`. The purge run delete on `ended_at` has no index, which is fine for this table size.
- **Controller migration rerun:** single V1 under Flyway. A rerun is a no-op. There is no rollback script; the schema is new, so rolling back means dropping the two tables and two functions (not tested).
- **Inventory V3 CHECK name:** V1 declares `kind text NOT NULL CHECK (kind IN (...))` inline on `stock_movement` with no name, so Postgres names it `stock_movement_kind_check` (`<table>_<column>_check`). There is no other check on `kind`, so the `DROP CONSTRAINT` matches. The new list is a superset, so existing SEED/RESTOCK/SHIPMENT/LATE_SHIPMENT rows revalidate. V3 runs in one Flyway transaction (transactional DDL), so a failure rolls it back entirely. `MigrationTest` covers rerun = no-op, the kind constraint still enforced, and that no sites were added.
- **Inventory rollback to the previous image:** V1/V2 are unchanged (checksums stable). Flyway's default `ignoreMigrationPatterns=*:future` lets the old image start with V3 applied. The old code never reads `kind`, `site_registration` or OPENING rows (grep), so it works. Not tested.
- **Inventory create-once concurrency** (`ReservationService.java` `createSite`/`createStock`, `InventoryStore.java:377-452`): both run inside `@Transactional`; store methods are `MANDATORY` and the enlisted connection is shared.
  - `INSERT ... ON CONFLICT DO NOTHING` under the default READ COMMITTED: a concurrent duplicate PUT blocks on the uncommitted row, then gets 0 rows. The follow-up `SELECT` (`siteStatus` / `openingQuantity`) is a new statement, so it sees the winner's committed row. The result is 200 for the same body and 409 for a different status or quantity. If the winner rolls back, the waiter inserts instead.
  - The registration/OPENING movement is in the same transaction as the row it describes, so neither can exist without the other.
  - `ux_stock_movement_one_opening` backs "one OPENING per record" at DB level.
  - A seeded (V2) record has no OPENING, so it returns 409 as documented.
  - Nothing updates or deletes existing rows. `site_registration` has immutable/no-truncate triggers reusing `reject_audit_change`.
- **Inventory restock idempotency** (unchanged): the per-reset keys `stardock-reset-<id>-<site>-<sku>` make a retried reset of the same id a no-op.
