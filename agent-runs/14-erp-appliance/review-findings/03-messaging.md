# Messaging (file exchange) pass, ERP commit 48aebae

Fresh-context subagent; findings 1-7 confirmed by experiments on an extracted copy. Repaired in ERP commit f15513c; the full suite (152 tests) and the harness (44 checks) were rerun afterwards (`evidence/05-after-review.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| M1 | High | One unreadable inbound file (e.g. mode 000 set by the SFTP client) aborts ingest every cycle and blocks every later file | Fixed: per-entry error handling and backoff; unreadable files quarantined unopened; `test_M1_…`; harness (mode 000 over SFTP) |
| M2 | High | A persistent move failure after commit re-publishes the result and adds audit rows every cycle | Fixed: an already recorded upload only finishes its move; `test_M2_…` |
| M3 | Med | Quarantine stored name includes the clock; ledger points at a missing file after a crash (same as A1) | Fixed with A1 |
| M4 | Med | Replay of a file whose bytes changed inserts a second row and leaves the first REPLAY_REQUESTED forever | Fixed: replay updates its own row by id; `test_M4_…` |
| M5 | Med | Oversized file read whole to hash (same as S2) | Fixed with S2 |
| M6 | Low | A second identical bad upload is quarantined without a row or ERR | Fixed: one record per upload (ingest_key), not per name and bytes; `test_M6_P8_…`; SPEC states it |
| M7 | Low | Directories and symlinks in inbound/ ignored silently; open() follows symlinks (with S4) | Fixed with S4; SPEC adds UNREADABLE (box1-ops-contracts 13fcfd2) |
| M8 | Low | One failing outbox row stops all publication (with S5) | Fixed with S5 |
| M9 | Info | Purge aborts on a concurrent delete (ENOENT) | Fixed: purge ignores vanished entries |
| M10 | Info | Same-millisecond revisions may publish out of order (same as A6) | Fixed with A6 |

No findings: outbox written in the business transaction, publish order and emit_seq guard, restart cleanup, duplicate byte identity, SPEC conformance, non-atomic writer handling, clock.
