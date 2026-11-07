# Messaging pass

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| M1 | High | ERR resends unbounded (same as P1) | **Fixed** (see persistence P1). |
| M2 | Medium | Credential, missing-database and read-only failures were not treated as outages, so valid events were dead-lettered after 20 attempts | **Fixed.** SQL states `28`, `3D`, `25006` and `55P03` count as outages, and a commit-time `RollbackException` holds the channel. |
| M3 | Medium | Events dead-lettered for `RETRIES_EXHAUSTED` had no `rejected_command` record | **Fixed.** Every dead-letter path records first. |
| M4 | Medium | An interrupt during a database hold could dead-letter a valid event at shutdown | **Fixed.** The retry sleep runs through interrupts; the process stops without committing the offset, so the event is redelivered. Not exercised at runtime. |
| M5 | Low | DLQ topic not yet in GitOps | **Open for the user.** box1-gitops#64 (D-009). |
| M6 | Low | Repeated quarantine records on failed moves (same as P2) | **Fixed.** |
| M7 | Low | Hidden names in `outbound/` may never be quarantined | **Confirmed and fixed.** The harness showed that Camel's SFTP consumer never lists dot-names (49/50 run). The new `outbound-hidden-sweep` route quarantines and moves them using the same key and strict host-key checking. Scenario check passes. |

Checked and correct: the outbox is written in the business transaction and published after broker confirmation; claims are restart-safe; the §7 table is applied in order; ERR files are deduplicated by `errorId`; resends are always equivalent and use fresh nonces; files move only after commit; order and inventory accept the events.
