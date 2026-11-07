# D-012 No customer recipients, contact data or identifiers

**Status:** user decision (2026-11-05), implementation rules decided by the run.

- Recipients are channel names from a fixed configuration map; no API or event can set a recipient.
- Parsing is allowlist-only: the consumer reads the envelope and, for the three consumed types, only the fields D-002 lists. `order.placed.v1` payloads are not parsed. `customerId` is never read into any object.
- No field outside the allowlist reaches a template, intent, receipt, outbox event, metric label or log line.
- Tests: an end-to-end test sends `order.placed.v1` with a sentinel `customerId` alongside the notice-producing events, then scans every table, every produced event, the API responses and the captured log output for the sentinel. The same scan runs in Phase 7 against the cluster API and pod log for a real order's `customerId`, without recording the value in run state.
- Known exception: the DLQ caveat in D-006.
