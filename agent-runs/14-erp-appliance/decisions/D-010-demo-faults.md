# D-010 Demo fault mode

- **Enable:** `demo_faults = true` in `/etc/box1-erp/erp.conf` (root-owned, read by the app). Off by default. When off, fault controls are absent from the TUI and the worker ignores any stored fault state.
- **Controls (TUI fault screen, only when enabled):** delay automatic processing by N seconds; pause/resume outbound publication; arm a one-shot crash after the next shipment commit and before its publication. Re-emission is a normal operator action, not a fault.
- **Stored and audited** in the ledger (`settings` + `audit` with actor `console`). Shown on the status bar while active.
- **One-shot:** the publisher disarms the crash in its own committed transaction, *then* calls `os._exit(70)`. On restart it is already disarmed, so there is no crash loop. systemd's restart delay and rate limit are the second guard.
- **No HTTP, no sudo:** the TUI changes only ledger rows the app user already owns; enabling demo mode needs root to edit the config file.
