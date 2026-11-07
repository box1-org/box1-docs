# D-003 Analysis lifecycle and in-memory state

**Status:** the store was decided by the user (in-memory, bounded); the values below are proposed.

- The operation ID is `ana_` plus a random UUID without dashes. The ID is not guessable and carries no data.
- Statuses: `QUEUED`, `RUNNING`, `COMPLETED`, `DEGRADED` (some evidence unavailable, analysis produced), `MODEL_UNAVAILABLE`, `MODEL_INVALID_OUTPUT`, `BUSY` (rejected at submit), `FAILED`.
  - `GET` on an unknown or evicted ID returns `404 ANALYSIS_NOT_FOUND`, with the body noting that analyses do not survive a restart.
- Store: a Caffeine cache with at most `AIOPS_ANALYSIS_MAX=200` entries and a TTL of `AIOPS_ANALYSIS_TTL=24h` after completion.
  - Each entry stores its caller's subject. `GET` is allowed for the creator and for any `aiops-viewer` (operator-only roles, D-005).
- The Deployment has `replicas: 1`, documented. With more than one replica, `GET` would miss analyses held on another pod, so scaling up is a follow-up that needs a shared store.
- No analysis is regenerated on read. A result is produced once, then served unchanged.
