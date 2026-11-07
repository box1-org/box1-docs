# Security pass (phase 5)

Reviewer: a fresh subagent given the diff `61bcb8c..bed8e44`, the prompt, the boundaries and the MCP extension docs. It made no changes; it ran `./mvnw -q test` (exit 0). Date: 2026-11-06 EST.

**Confirmed sound:**
- `Guard` runs before every upstream read on REST and MCP. It checks the azp allowlist, requires a JWT outside the test profile, takes roles from this client's claim only, pins the audience, and has introspection off.
- The model gets no tools, and tool calls are rejected.
- Evidence goes only in the user message, the system prompt is constant, the schema is validated on the server, citations are checked and actions are allowlisted.
- IDs are pattern-checked before any URL is built, and redirects are off.
- Error text is fixed and never echoes model output.

No high-severity findings.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| S-1 | medium | An upstream that sends headers and then stalls its body blocks the single analysis worker indefinitely, after which every analysis gets 429 | **Repaired in `0cf2604`.** Repair: put an overall deadline on each upstream read (`sendAsync().get(timeout)` with cancel), and test it with a stalling stub |
| S-2 | medium | Window payloads have no field-count or byte bound, so 20,000 events × 64 KiB risks an OOM | **Repaired in `0cf2604`.** Repair: a per-event-type field allowlist from the contract schemas (this also covers S-3) |
| S-3 | low | Payload fields the contract doesn't list (for example on notification events) reach the model and MCP viewers | **Repaired in `0cf2604`.** Repair: same allowlist as S-2 |
| S-4 | low | The HTTP policy only requires authentication, so any realm token with the audience can open MCP and list the tools (no data leaks) | **Repaired in `0cf2604`.** Repair: an HTTP `roles-allowed=aiops-viewer,aiops-analyst` policy on `/mcp*` and `/api/v1/ai/*`. `Guard` stays |
| S-5 | low | The audit log records unvalidated caller text | **Repaired in `0cf2604`.** Repair: log the ID only when it matches an `Ids` pattern, otherwise log `invalid` |
| S-6 | low | A fulfillment or reservation record isn't checked against the requested order, so a mis-keyed ID could attach another order's record | **Repaired in `0cf2604`.** Repair: if the record's `orderId` differs, drop the data and mark the source `CONFLICTING` |
| S-7 | low | The model response is fully buffered before its size is checked | **Repaired in `0cf2604`.** Repair: stream it, reading at most `MAX_RESPONSE_BYTES+1` |

Not a finding: `/q/openapi` and Swagger are public. They hold only the contract.
