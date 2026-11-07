# D-008 SQLite settings and race strategy

- `journal_mode=WAL` (readers never block the writer; the TUI can read while the worker writes), `synchronous=FULL` (a committed shipment survives power loss), `foreign_keys=ON`, `busy_timeout=5000` ms as the bounded lock wait.
- Every mutation runs in `BEGIN IMMEDIATE … COMMIT` inside one domain function; nothing waits for user input or file I/O inside a transaction. The TUI confirms first, then calls the domain function.
- Optimistic version check: `requests.version` increments on each change; a mutation states the version it read (`UPDATE … WHERE request_id=? AND version=?`). A stale TUI action fails with "changed by someone else, refreshed" instead of overwriting.
- Database constraints back the rules: `UNIQUE(fulfillment_request_id)` on requests and on shipments, `UNIQUE(fulfillment_request_id, revision)` on results, CHECK constraints on states.
- A manual ship racing an automatic ship: both run `ship()`; the second sees a terminal state (or loses the version check), and `UNIQUE` on shipments is the backstop. Exactly one shipment.
