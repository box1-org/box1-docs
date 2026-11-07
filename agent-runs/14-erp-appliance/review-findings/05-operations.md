# Operations pass, ERP commit 48aebae

Fresh-context subagent; reproduced O1 in a scratch extract, timed O10 at 10k rows. Repaired in ERP commit f15513c; the full suite (152 tests) and the harness (44 checks) were rerun afterwards (`evidence/05-after-review.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| O1 | High | Restore with the console open splits the ledger (reproduced); a hung worker passes the heartbeat check (same as A2) | Fixed with A2; the watchdog covers a hung worker (O5) |
| O2 | High | sysusers IDs not fixed: a rebuilt guest with the kept data disk may not own its ledger | Fixed: sysusers IDs 961/962/963; harness checks them |
| O3 | Med | VM-INTEGRATION gaps: bind-mount layout (EXDEV across mounts), `/etc/box1-erp` not created, `box1-erp` not on PATH, no VM sizing, exchange recreated on root fs when the volume is missing | Fixed: one volume at /srv/box1-erp, provisioning script (refuses without a mount, never deletes), /usr/bin/box1-erp, install -D, sizing proposal, sshd RequiresMountsFor advice; tmpfiles removed |
| O4 | Med | `status` always exits 0 and has no lag ages | Fixed: status --check exits 0/1/2; oldest pending, unpublished and quarantine ages; `test_O4_…`, harness |
| O5 | Med | Hard start limits leave a blank console or a dead worker after a transient fault; no watchdog for a hung worker | Fixed: no hard start limits; restart backoff (worker 5 s to 5 min, console 2 s to 1 min); worker Type=notify with WatchdogSec=60; harness froze the worker and the watchdog restarted it |
| O6 | Med | Schema version never checked; no upgrade path | Fixed: user_version checked on open; `box1-erp migrate` under the exclusive lock; runbook upgrade section; `test_O6_P7_…` |
| O7 | Low | Heartbeat only per cycle: false UNRESPONSIVE in large batches | Fixed: heartbeat and watchdog inside long loops, throttled to 2 s |
| O8 | Low | Runbook: PATH, status, rebuild, upgrade, broken-console steps | Fixed: runbook PATH, status, rebuild, upgrade and broken-console steps |
| O9 | Low | Correlation IDs missing on ship/publish/quarantine log lines; 1 s timestamps | Fixed: correlation_id, traceparent and file_id on ship, publish and quarantine lines; millisecond timestamps |
| O10 | Low | Console full rescan every second: 17–26 ms at 10k rows on the Mac | Fixed: index on updated_at; console re-reads rows only when PRAGMA data_version changes or after its own action |
| O11 | Note | Console unit never started on a TTY (already #25 evidence) | recorded |

No findings: exit-code handling, memory limits, poll interval, Type=idle/Conflicts/TERM, in-process ledger retry in the console, backup method, missing-ledger guard.
