# Persistence pass, ERP commit 48aebae

Fresh-context subagent; findings 1-4 demonstrated with scripts on an extracted copy. Repaired in ERP commit f15513c; the full suite (152 tests) and the harness (44 checks) were rerun afterwards (`evidence/05-after-review.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| P1 | High | Restore under a running TUI: console writes go to the unlinked old file (demonstrated; same as A2, O1) | Fixed with A2 |
| P2 | High | Restore to an older point allows a second shipment and reused revision numbers, unlinks post-backup archive copies and the old ledger; runbook claim about duplicates is wrong | Fixed: divergence check refuses unless --accept-divergence; previous ledger and spool kept; restored ledger in MANUAL; runbook corrected; `tests/test_backup.py::test_restore_to_an_older_point_is_refused_unless_accepted` |
| P3 | Med | Quarantine stored name not idempotent across a crash (same as A1, M3; demonstrated) | Fixed with A1 |
| P4 | Med | A failed COMMIT leaves the transaction open and the write lock held; ROLLBACK errors mask the cause (demonstrated) | Fixed: a failed COMMIT rolls back and ROLLBACK errors no longer mask the cause; `test_P4_…` |
| P5 | Low | Backup aborts if a file vanishes during tar; partial backup directory blocks the label | Fixed: backup writes to a partial directory and renames; regular files only; vanished files skipped |
| P6 | Low | Missing CHECKs on outbox kinds, shipment FK, reject code/text pairing | Fixed: outbox kind CHECKs, requests.shipment_id foreign key, reject code and text pairing |
| P7 | Low | No migration story (same as O6) | Fixed with O6 |
| P8 | Low | Same-name same-bytes re-upload after quarantine gets no ERR (same as M6) | Fixed with M6 |

No findings: BEGIN IMMEDIATE and version checks, ship race, revision allocation, ship atomicity, no transaction across input or I/O, emit_seq, recovery after restart, WAL read lengths, BUSY surfacing, online backup consistency, WAL/SHM removal on restore, indexes at 5k rows (7.5 ms list query).

Release pass: not applicable. This run publishes no image, GitOps change or deployment; the pinned artifact is blocked on D-001/D-002.
