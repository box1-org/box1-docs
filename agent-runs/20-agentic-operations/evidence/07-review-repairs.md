# Phase 5 review repairs

Repaired on agentic-operations `issue-20-agentic-operations` at **`0cf2604`** (2026-11-06 EST), after the five reviewer passes in `review-findings/`.

| Finding | Change | Test |
|---|---|---|
| S-1, S-7, O-2 | `BoundedHttp`: one overall deadline (`sendAsync().get()` plus cancel) and a subscriber capped at `max+1` bytes, used by `HttpUpstreams` and `VllmModelClient` | `BoundedHttpTest` (stalled body times out in under 3s; large body stops at the cap) |
| S-2, S-3 | `EvidenceWindow.KEPT`: payload field allowlist per event type, from contracts `events/v1` at `bb381b0` | `EvidenceWindowTest.payloadKeepsOnly…` |
| S-4 | HTTP policy `roles-allowed=aiops-viewer,aiops-analyst` on `/api/v1/ai/*` and `/mcp*` | `McpToolsTest.callersWithoutAnAiopsRoleCannotConnect` (403); prod jar: anonymous 401 |
| S-5 | `ToolAudit.loggableId` | `ToolAuditTest` |
| S-6 | `EvidenceService.belongsTo`, giving `CONFLICTING` with no data | `AnalysisApiTest.aReferencedRecordOfAnotherOrderIsNotEvidence` |
| A-1 | Uncited summary replaced, with `statusDetail` set | `AnalysisApiTest.anUncitedDiagnosisIsNotShownAsTheSummary` |
| A-2 | Execute first, then `putIfAbsent` | `AnalysisApiTest.theQueueIsBounded…` (accepted IDs stay readable after BUSY) |
| A-4 | `IncidentRules` matches the console's `current()`; `minutesAwaitingErp` added to the prompt | `IncidentRulesTest` |
| A-6, O-1 | OTel `Context.wrap`, `aiops.analysis` span, `analysisId` in MDC, W3C `traceparent` injected on outbound calls | Compile and existing tests. Live trace linkage is to be checked at phase 7 |
| A-7 | TTL counts from completion | `AnalysisStoreTest.updatesKeepTheOriginalExpiry` (still passes: an unfinished entry expires from creation) |
| M-2 | `AIOPS_CONSUMER_GROUP`; one replica with `Recreate` documented | Config. The Recreate strategy goes in the runtime PR |
| M-3 | `forCorrelation` index; `list_recent_events` accepts `correlationId` | `EvidenceWindowTest.eventsCanBeFoundByCorrelation`, `McpToolsTest.viewerReadsEvidence…` |
| M-4 | Pruning by scan on `occurredAt`; oldest age by scan | `EvidenceWindowTest.outOfOrderEvents…` |
| M-5 | `schemaVersion == 1` and `causationId` required | `EvidenceWindowTest.envelopeNeedsSchemaVersion…` |
| M-6 | Seek failure caught, WARN logged, `aiops_window_seek_failures_total` counted | `WindowStartSeekTest` |
| O-3, O-4 | Abandoned work logged and counted; first `org.box1` frame logged | Inspection |
| O-5, R-3 | Runbook corrected; MCP version note; smoke gap stated | Docs |

**Not repaired in code:**
- M-1, A-3, R-1: these are the contracts, Keycloak and workloads PRs, still to be opened.
- M-7: accepted at lab volumes.
- R-2: the shared smoke task is platform-owned. Live acceptance checks it by hand, and a follow-up is to be filed.
- WR-1 to WR-4: belong in the runtime PR.

**Verification:**
- `./mvnw -B -ntp verify`: 69 tests, 0 failures, 0 Checkstyle violations.
- Production-profile jar, with Kafka and the model unreachable:
  - ready: 200
  - anonymous analyze: 401
  - forged token: 401
  - anonymous `/mcp`: 401
  - `/api/info`: 200
  - token strings in the log: 0
  - ERROR lines: 0
