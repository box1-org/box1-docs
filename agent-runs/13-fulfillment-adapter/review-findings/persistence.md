# Persistence pass

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| P1 | High | ERR-driven resends were never bounded: a successful upload reset the counter, and the resend had no backoff | **Fixed.** A separate `err_resends` counter that uploads never reset, exponential backoff, and `ERR_RESENDS_EXHAUSTED` after 5. Test: `ResultIngestionTest.repeatedTransportErrsAreBoundedWithBackoff`. Also found independently by the messaging pass. |
| P2 | Medium | A file whose move to `consumed/` keeps failing is re-recorded on every poll | **Fixed.** Receipts are unique on (name, SHA-256, outcome) with `ON CONFLICT DO NOTHING`; the quarantine metric counts only new records. Test: `aFailedMoveDoesNotMultiplyQuarantineRecords`. |
| P3 | Low | A late upload failure could overwrite a shipped request or a `CONFLICTING_REUSE` hold | **Fixed.** `uploadFailed` changes state only while `QUEUED`; `applyResult` resets the transport budgets. |
| P4 | Low | The dispatch lease could expire mid-batch | **Fixed.** Batch 10, lease 600 s; a connection-level failure releases the rest of the batch unattempted. |
| P5 | Low | A failure while recording a successful upload was logged as a transport failure | **Fixed.** Only framing and transfer are inside the catch. |
| P6 | Low | Missing CHECKs on `pending_upload_reason` and `erp_result.status`; no index for the outbox claim | **Fixed** in V1, which has never been deployed. The local database was recreated. Rollback is restore-from-backup; documented as untested. |
| P7 | Low | Retention compares the SFTP mtime with the pod clock | **Documented** in the runbook. |
