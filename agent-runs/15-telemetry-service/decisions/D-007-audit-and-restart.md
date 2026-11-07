# D-007 Run audit storage, retention and restart behavior

**Status:** decided by the agent, Phase 1.

- **Storage:** the service's own PostgreSQL, tables `control_run` (one row per run: id, kind LOAD/CHAOS, actor, seed, configuration, state, armed/started/stopped times, stop reason, owner instance, heartbeat, sequence digest, counts) and `control_audit` (append-only: run id, at, actor, action, detail JSON). Actions: `ARM`, `START`, `INJECT` (catalog entry + parameters), `STOP`, `STOP_ALL`, `TTL_EXPIRED`, `ABORTED_RESTART`, `RESET`, `DENIED` (gate or cap refusals).
- **Actor:** the token's `preferred_username` claim, falling back to `sub`. Never the request body.
- **Retention:** 90 days, deleted by the same retention job as readings (D-009). Audit rows are never updated, only inserted; a database trigger rejects UPDATE and DELETE except the retention delete, which runs as a function that disables it for old rows only.
- **Restart:** runs execute in one pod. Each active run has an owner instance ID (random per process) and a heartbeat every 5 s. At startup, and every 10 s, the reaper marks any run that is `ARMED` or `RUNNING` with a different owner or a heartbeat older than 20 s as `ABORTED` with `ABORTED_RESTART`, and never restarts it. A restarted pod therefore starts with no runs, and its first action is to record the abort.
- **Honest state:** the page polls `GET /api/v1/control/state`. If the call fails or times out, the page shows `UNKNOWN`, not the last value. The server's state includes `confirmedAt`, and the page shows `UNKNOWN` if it is older than 15 s.
- **Reset:** `POST /api/v1/control/reset` stops all runs, resumes the producer and clears in-memory fault state, and records `RESET`. It deletes no readings, alerts or audit rows.
