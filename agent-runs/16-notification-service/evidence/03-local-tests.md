# Phase 3–4 local tests

Commit `385ca47ea042ace5a35744e7b4143475e2fa2f57` (notification-service branch `issue-16-notification`). Run 2026-11-06 05:13–05:17 UTC (00:13–00:17 EST). Host and Podman VM clocks agreed (05:13:15 / 05:13:16 UTC). Podman 5.7.0, Testcontainers images `postgres:15-alpine` and `apache/kafka:4.2.0`, named `run16-*`.

## Commands and results

```sh
export DOCKER_HOST=unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}') TESTCONTAINERS_RYUK_DISABLED=true
./mvnw -B -ntp verify -Pcontainers -DskipITs=false
```

- Surefire: `Tests run: 53, Failures: 0, Errors: 0, Skipped: 0`
- Failsafe: `Tests run: 7, Failures: 0, Errors: 0, Skipped: 0` (GreetingResourceIT 5, ProcessRestartIT 2)
- `You have 0 Checkstyle violations.`, SpotBugs + FindSecBugs `BugInstance size is 0`, `BUILD SUCCESS`

Earlier runs on earlier commits failed and were repaired (pilot-log repairs 3–5); this is the run on the commit kept for review.

## Scenario → test

| Prompt scenario | Test | Observed |
|---|---|---|
| Duplicate event | `ScenariosTest.duplicateShippedEventGivesOneIntentAndOneDelivery` | 1 intent, 1 processed source, 1 receipt, 1 `notification.delivered.v1` (second read waits 15 s for a second record; none) |
| Same fact through two events | `sameFactFromTwoEventsGivesOneIntentAndOneDelivery`, `nonRetryableFailureAndTheResultingExceptionAreOneNotice` | 1 intent with 2 sources, 1 receipt, 1 event; API `sources.size()==2` |
| Retryable shipment failure produces a notice | `retryableShipmentFailureStillProducesAnOperatorNotice` | `SHIPMENT_DELAYED` on `ops-fulfillment`, DELIVERED, exact text checked |
| Stub 503 then recovery | `stub503ShowsIncreasingAttemptsThenSuccess` | attempts 1,2,3 = TRANSIENT(503), TRANSIENT, SUCCESS; increasing `started_at`; API attemptCount 3, failure null |
| Permanent 4xx not retried | `permanentFourHundredIsNotRetried` | 1 attempt, FAILED / PERMANENT_REJECTION / PROVIDER_REJECTED / 422; failed event httpStatus 422 |
| Retry exhaustion gives FAILED | `retryExhaustionEndsFailedAndStopsRetrying` | 6 attempts, FAILED / RETRIES_EXHAUSTED / 503; still 6 attempts 2.5 s later |
| Poison to DLQ and replay | `poisonRecordsReachTheDeadLetterTopicUnchangedAndReplay` | bad JSON and a misrouted event on the DLQ byte-identical, headers `dead-letter-topic`, `dead-letter-reason`; replay (twice) of the misrouted record to the right topic gives 1 delivered notice |
| Shutdown with a retry pending | `ProcessRestartIT.shutdownWithARetryPendingResumesAfterRestartWithoutADuplicateDelivery` (packaged jar, prod profile, SIGTERM) and `ScenariosTest.aWorkerThatDiesAfterTheProviderAcceptedCausesNoSecondDelivery` | after restart: DELIVERED at attempt 2, 1 receipt, 1 event; after a dead worker's accepted call: same receipt reused |
| Template injection escaped | `TemplatesTest` (CI) | markup, CR/LF, U+2028, bidi, `|`, backtick, links neutralised; 10 000-char value capped |
| No customer identifier anywhere | `noCustomerIdentifierAppearsAnywhere`, `EventParserTest.orderPlacedIsEnvelopeOnly…` | sentinel `customerId` absent from all 8 tables (`row_to_json`), produced events, API response and every captured log line (capture confirmed it saw the order's lines) |
| Anonymous request | `SecurityTest.anonymousRequestsGet401ProblemJson` (CI), `readerSees…` | 401 Problem JSON with `WWW-Authenticate: Bearer` on all `/api/v1` paths |
| Request without the reader role | `SecurityTest.tokensWithoutTheReaderRoleGet403` (CI), `readerSees…` | 403 for no role, groups-only, other `azp`, fault-operator-only |
| Fault control outside the allowlist | `SecurityTest` (CI: FAULTS_DISABLED), `NotAllowlistedNamespaceTest` | 403 `NAMESPACE_NOT_ALLOWLISTED`, audited with actor and namespace, no fault row |
| Fault TTL expiry | `aFaultExpiresOnItsTtlWithAnAuditEntry` | 10 s fault gone from API within 20 s; `EXPIRED` audit row; next delivery 1 attempt |
| Broker outage → bounded outbox, later delivery | `brokerOutageLeavesABoundedOutboxBacklogThatPublishesLater` | Kafka container paused: notice DELIVERED, 1 unpublished outbox row, readiness 200; after unpause published once |
| Floor (offset policy) | `eventsBeforeTheFloorProduceNoNotice` | pre-floor event: no notice, no processed_event row |
| Fault bounds server-side, audit immutable | `faultBoundsAreEnforcedServerSideAndAudited`, `theAuditTrailCannotBeChanged`, `aFaultOperatorWithoutTheReaderRoleCanSetAndClear` | 7 out-of-bounds bodies → 400, each audited `REFUSED_*` with actor; UPDATE/DELETE/TRUNCATE rejected by trigger |
| Startup safety | `ProcessRestartIT.refusesToStartWithInvalidSafetyConfiguration` | missing/future floor, max-attempts 50, TTL cap 86400, provider `smtp` each exit non-zero with the reason |
| Metrics | `readerSeesTheNoticeAndATokenWithoutTheRoleIsRefused` | `box1_notification_pending`, `_oldest_pending_age_seconds`, `_delivery_attempts_total`, `_delivered_total`, `_failed_total{category="RETRIES_EXHAUSTED"}`, `_events_consumed_total`, `box1_outbox_pending` present |
| Console token (proposed D-007) | `ConsoleTokenTest` (CI) | with the console client configured: viewer/operator read, developer 403, never fault control |
