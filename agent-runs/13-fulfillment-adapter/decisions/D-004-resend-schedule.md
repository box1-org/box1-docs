# D-004 Upload timeout, resend schedule and needs-attention

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Decision:**
- *Upload failure* (SFTP connect, auth, host key, I/O): retry with backoff 10 s doubling to 5 min, at most 40 attempts (about 3 hours), then needs-attention `UPLOAD_EXHAUSTED`.
- *No acknowledgement* (no `RES` for the request) after a successful upload: equivalent resend under a new nonce after 2 min, doubling to a 60 min cap, at most 8 uploads without acknowledgement (about 4 hours), then needs-attention `NO_ACKNOWLEDGEMENT`.
- *Acknowledged, not terminal* (`PENDING` or `HELD`): waiting is never a failure. A slow equivalent-resend probe every 6 h recovers a lost later result; it is not counted as a retry and never leads to needs-attention.
- Any valid result clears needs-attention and is applied by the section 7 table. A late acknowledgement is never lost.
- `POST /internal/fulfillments/{id}/reconcile` (role required, audited) restarts dispatch with a fresh budget.
- All timing uses database `now()`.

**Consequences:** AUTO imports within about 1 s of upload, so 2 min is generous; MANUAL still imports and publishes revision 1 immediately, so manual waits never trigger resends.
