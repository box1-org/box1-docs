# Phase 5 reviewer repairs and rerun

Six fresh-subagent passes reviewed `385ca47` (findings in `review-findings/`). Repairs landed in notification-service `8b8c27698760ebbc91e50ea86ea91507ded1cdad`.

## Full suite after repairs (local)

2026-11-06 05:28–05:32 UTC. Host and Podman VM clocks agreed (05:27:55 and 05:27:56 UTC).

```sh
./mvnw -B -ntp verify -Pcontainers -DskipITs=false
```

| Result | Value |
|---|---|
| Surefire | `Tests run: 57, Failures: 0, Errors: 0, Skipped: 0` |
| Failsafe | `Tests run: 7, Failures: 0` (`ProcessRestartIT` 2, `GreetingResourceIT` 5) |
| Checkstyle violations | 0 |
| SpotBugs BugInstance | 0 |
| Build | `BUILD SUCCESS` |

The first rerun after repairs (05:24 UTC) failed one assertion. The 401/403 denial audit ran on the Vert.x event loop, where the blocking insert is refused. The denial itself was still enforced. The audit write now runs on a worker thread, with the actor captured before offload. The "denial not audited: StoreException" warnings in the passing run come from `SecurityTest`, which runs without a database, and are expected there.

New or changed tests:

| Test | Shows |
|---|---|
| `ReplayTest` | A misrouted record reaches the DLQ and is replayed once by the group-scoped channel. The garbage record stays dead-lettered. Nothing is produced to the shared fulfillment topic. |
| `ScenariosTest.poison…` | An unknown event type is acknowledged and counted, not dead-lettered. |
| `ScenariosTest.faultBounds…` | `DENIED_FORBIDDEN` and `DENIED_UNAUTHENTICATED` audit rows are written. `actor_subject` is recorded. |
| `SecurityTest` | An ID token gets 401. |
| `TemplatesTest` | Shared facts render identically from either event. Truncation does not split a surrogate pair. |
| `EventParserTest` | Unknown type versus known type on the wrong topic. |

## CI

PipelineRun `box1-ci/notification-service-validate-7gp7r` **Succeeded** at 2026-11-06T05:34:08Z on `8b8c276`:

- Surefire 38/38 and Failsafe 5/5 passed.
- 0 Checkstyle violations; `BugInstance size is 0`; `BUILD SUCCESS`.
