# D-005 ERR handling by code

**Status:** decided by the agent in Phase 1, 2026-11-05.

An `ERR` is matched to an upload by `inboundFileName`; it never changes business state.

| Codes | Meaning for the adapter | Action |
|---|---|---|
| `TRUNCATED`, `COUNT_MISMATCH`, `ENCODING`, `UNREADABLE` | transport damage or permissions; the adapter self-validates every file before upload, so bytes it sent were valid | equivalent resend under a new nonce with backoff, at most 5 (`err_resends`, never reset by an upload), then needs-attention `ERR_RESENDS_EXHAUSTED` (revised after review finding P1) |
| `FILE_TOO_LARGE`, `MALFORMED_RECORD`, `UNSUPPORTED_VERSION`, `RECORD_ORDER`, `MISSING_FIELD`, `FIELD_LENGTH`, `FIELD_VALUE`, `FILENAME_MISMATCH` | the same bytes would fail again; an adapter defect or a protocol disagreement | needs-attention `ERP_REJECTED_FILE:<code>` |
| `CONFLICTING_REUSE` | the ERP holds a different request under this ID | needs-attention `CONFLICTING_REUSE`; never resend a different request |
| unknown upload name | not ours or already purged | recorded as unmatched, metric, no state change |

An ERR for an upload whose request is already acknowledged is recorded only, except `CONFLICTING_REUSE`, which always moves the request to needs-attention. Every ERR increments `fulfillment_erp_errors_total{code}`.
