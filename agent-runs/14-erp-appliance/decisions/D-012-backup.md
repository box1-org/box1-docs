# D-012 Backup method

`box1-erp backup` uses the SQLite online backup API (`Connection.backup`) to `backups/ledger-<UTC>.db`, then runs `PRAGMA integrity_check` on the copy, then tars the spool (`archive`, `quarantine`, and unconsumed `inbound`/`outbound`) beside it with a manifest of row counts and sha256s. `box1-erp restore` runs only with the worker stopped, verifies the manifest, and places the files. A blind copy of a live `ledger.db` is not used.

**Where #25 stores it:** a decision for #25 (NooBaa has availability problems, #43). This run proves backup and restore in the container harness only.
