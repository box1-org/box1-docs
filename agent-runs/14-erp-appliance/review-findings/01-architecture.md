# Architecture pass, ERP commit 48aebae

Fresh-context subagent given the code, prompt 04, issue #14 and ERP1 SPEC. No experiments run. Repaired in ERP commit f15513c; the full suite (152 tests) and the harness (44 checks) were rerun afterwards (`evidence/05-after-review.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| A1 | Med | Quarantine stored name includes the clock; after a crash before the move, the file lands under a new name the ledger does not know, and a later replay reports it missing | Fixed: deterministic per-upload stored name; `tests/test_review_regressions.py::test_A1_M3_P3_quarantine_name_survives_a_crash_before_the_move` |
| A2 | Med | Restore replaces the ledger file and deletes -wal/-shm under a running TUI, whose connection keeps writing to the old file | Fixed: ledger lock; restore needs it exclusively; console takes it shared and reconnects; runbook stops consoles; `tests/test_backup.py`, harness |
| A3 | Med | Ledger screen lacks the required origin and line columns | Fixed: `O` (origin) and `LN` (line count) columns, `~` on cut values; asserted in `tests/test_tui.py` |
| A4 | Low | TUI always passes demo_enabled=True; the domain's demo gate never applies | Fixed: TUI passes `cfg.demo_faults` |
| A5 | Low | OUT column cannot show a failure; republish clears last_error | Fixed: `FAIL` publication state; republish keeps `last_error` |
| A6 | Low | Publication order within one millisecond falls back to a random result ID | Fixed: publish orders by `created_at, request_id, revision` |
| A7 | Low | Crash fault fires on any pending SHIPPED result, including a re-emission | Fixed: crash fault only on a SHIPPED result never published before; `test_A7_…` |
| A8 | Low | Replayed files stay in quarantine; symlinks and other non-regular inbound entries are skipped silently | Fixed: replayed file moves to the archive; non-regular inbound entries quarantined as UNREADABLE (M7) |

No findings: state ownership, shared domain layer (apart from A4), explicit transitions, business vs publication state, commit ordering (apart from A1), #25/#13 boundaries, out-of-scope items, detail screen, search/filter, visibility distinctions.
