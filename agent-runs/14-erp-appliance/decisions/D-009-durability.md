# D-009 Publication durability and crash windows

**Atomic visibility:** write `.<ready-name>.tmp` in the target directory, then `rename` to the ready name. Readers only match ready names.

**Durability (separate from visibility):** write → `fsync(file)` → close → `rename` → `fsync(directory)`. Only after the directory fsync does the worker mark the result `PUBLISHED` in the ledger.

| Crash point | Outcome on restart |
|---|---|
| After ship commit, before temp write | Intent is `PENDING_PUBLISH`; published from the ledger |
| After temp write, before rename | Stale `.tmp` ignored by readers, removed at startup; republished |
| After rename, before dir fsync or ledger mark | Republished with the same name and bytes; harmless duplicate |
| Inbound: after ledger commit, before archive move | File re-read, equivalent → latest result re-published, then archived |

The adapter writes inbound files with the same temp-then-rename rule; over SFTP it cannot fsync, so the ERP treats a ready inbound name as complete and validates the trailer count to detect truncation.
