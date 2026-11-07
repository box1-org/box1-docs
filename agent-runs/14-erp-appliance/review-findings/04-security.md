# Security pass, ERP commit 48aebae

Fresh-context subagent; experiments in a scratch extract only. No live weakness in a shared system: every finding is in unmerged run code that is not deployed anywhere. Repaired in ERP commit f15513c; the full suite (152 tests) and the harness (44 checks) were rerun afterwards (`evidence/05-after-review.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| S1 | Critical | Outbound temp file opened with O_CREAT\|O_TRUNC and no O_NOFOLLOW: the SFTP account can plant a symlink at `.RES….tmp`, and the next republish (an equivalent repeat request suffices) overwrites the ledger. Demonstrated in the scratch extract | Fixed: random temp names with O_EXCL and O_NOFOLLOW; rename replaces a planted link; `test_S1_…`; harness plants the link over real SFTP, ledger intact |
| S2 | High | Oversized inbound file is read whole to hash it (and on EXDEV copy): memory over MemoryMax, restart loop, worker down after StartLimitBurst | Fixed: chunked hashing, prefix-only storage; `test_S2_M5_…` (peak under 4 MiB for 40 MiB) |
| S3 | Med | Archived/quarantined inbound inode stays owned and writable by erpsftp (hardlink kept in consumed/); replay reads attacker-changed bytes | Fixed: uploads copied into application-owned files, then unlinked; `test_S3_…` |
| S4 | Low | Scan-to-open race: read_bounded follows symlinks | Fixed: O_NOFOLLOW and O_NONBLOCK with an fstat regular-file check; links quarantined unopened; `test_M7_S4_…` |
| S5 | Low | A directory planted at a final outbound name stops all publication | Fixed: a directory at a result name fails that result alone, with backoff; `test_S5_M8_…` |
| S6 | Low | Missing SystemCallFilter, ProtectProc, RemoveIPC; worker ReadWritePaths includes backups/ | Fixed: SystemCallFilter, ProtectProc, ProcSubset, RemoveIPC; backups read-only; offline exposure 1.1 worker, 1.3 console |
| S7 | Low | Console has no authentication; runbook should state the trust model | Fixed: RUNBOOK "Trust model" |
| S8 | Info | Re-enabling demo faults re-activates stored fault settings (e.g. an armed crash) | Fixed: worker clears stored faults at start when demo is off (audited FAULT_RESET); `test_S8_…` |

No findings: secrets and data in source/fixtures, log injection (ensure_ascii), path traversal, TUI escapes, demo-fault gating by root-owned config, chroot ownership, backup/restore extraction, supply chain.
