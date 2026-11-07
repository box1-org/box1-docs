# Security pass

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| S1 | Medium | An unhandled exception on a REST path returned a stack trace and copied request headers, including `Authorization`, into the response | **Fixed.** A route-scoped `onException` on each REST route returns a fixed problem document after removing all headers. `StoreException` is handled in `reconcile`. Harness check: an operator call during a database outage gets a 503 problem with no echoed header or token. My first fix made the handler global, which on the file routes would have moved uncommitted files; I caught that before running it. The suggested `muteExceptions` option does not exist on `platform-http` in Camel 4.22 (startup failed), so it is not used. |
| S2 | Medium | Outbound files were read whole into memory with no limit | **Fixed.** `streamDownload=true`, and at most 65,537 bytes are read, so a larger file fails the ERP1 size check and is quarantined as `INVALID_FILE_TOO_LARGE` with its size and no bytes. Not exercised with a large file at runtime. |
| S3 | Low | Test scripts interpolated arguments into Python and SQL | **Fixed.** The harness passes values as environment variables, and scenario IDs are validated where they are generated. |
| S4 | Info | `00-discovery.md` described the adapter namespace's missing NetworkPolicy and the template's gate default | **Fixed.** Replaced with pointers. |

Checked and correct: anonymous writes are refused on all write and internal paths; the JWT checks issuer, audience and client role; there is no accept-new host key path; file names are generated and outbound names sanitised; `reasonText` never appears in events, the API or logs; SQL is parameterised; there are no secrets in source or evidence.
