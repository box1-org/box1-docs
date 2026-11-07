# Contract review of box1-ops-contracts#6, first revision (b6e6731)

Fresh-context subagent, given the PR, the #14 and #13 prompts, issue #13 and the event schemas; not the design reasoning. Run before Phase 4 on purpose: see pilot-log ambiguity 3. All findings repaired in b20694c and retested (`evidence/02-contracts.txt`).

| # | Sev. | Finding | Outcome |
|---|---|---|---|
| 1 | High | No rules or fixtures for conflicting, late or out-of-order results (#13 needs them) | SPEC section 7 consumer table; `sequences` in the manifest (3 sequences, 15 deliveries); reference `consume()` |
| 2 | High | Field count checked before magic, so a reshaped v2 header gives `MALFORMED_RECORD`; long magic gives `FIELD_LENGTH` | Version read from `HDR\|ERP<n>` at step 4, before records; fixtures `version-2-new-shape`, `version-long`, `first-record-not-hdr` |
| 3 | High | Camel Bindy cannot do backslash escapes, code-point lengths or the validation order | SPEC section 9: adapter needs its own framing step; Bindy only for typed mapping |
| 4 | Med | Name checked last in section 3 but first in section 4 | Name is step 0 and fixes the expected type; fixture `bad-name-bad-content` |
| 5 | Med | HDR field lengths undefined | HDR table has Req./Max; file type must equal the name's (`header-says-res`) |
| 6 | Med | Re-emitted results collide when moved into `consumed/` | Moves go to `consumed/<name>.<nonce>` |
| 7 | Med | Quarantined outbound files would be reprocessed | Adapter moves them to `consumed/` too |
| 8 | Med | `ERR.inboundFileName` may be unwritable | Decode with U+FFFD, `?` for controls, 255 code points |
| 9 | Med | Ledger commit order before archive move unstated | SPEC section 4 "Commit order"; adapter may resend equivalent requests |
| 10 | Med | Broken `fixtures/mapping/` link | Link removed; manifest `mapping` described |
| 11 | Low | Timestamp year range, leap second, sub-ms rounding | 1970–9999, no `:60`, truncate; fixtures `year-0001`, `leap-second` |
| 12 | Low | Unicode normalization | Exact code-point comparison stated |
| 13 | Low | Inbound accepting non-REQ types only by accident | Expected type comes from the name |
| 14 | Low | Fixture `createdAt` earlier than `statusAt` | RES fixtures use `createdAt` = `statusAt` |
| 15 | Low | No unexpected outbound names in `names` | Added `notes.txt` and a REQ name in `outbound` |
