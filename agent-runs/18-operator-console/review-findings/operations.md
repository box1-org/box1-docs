# Review pass: Operations (fresh subagent, operations-console d007f00)

The reviewer ran the prod jar locally with Keycloak and the upstreams unreachable, and read the cluster read-only.
- Readiness is independent of upstreams and Keycloak.
- Trace IDs reach the MDC with exporter `none`.
- The read-only root filesystem is fine (`/tmp`).
- The template pod uses 105 MiB.

| ID | Sev | Finding | Outcome |
|---|---|---|---|
| OPS-1 | Med | No per-request or per-upstream-failure log lines, so the runbook's "search the logs by trace ID" finds nothing | **Fixed**: WARN per failed upstream call (no URL/headers/body) |
| OPS-2 | Med | Keycloak down: page loads return 500, logs flood, and the runbook doesn't cover it | **Fixed (runbook)**: Keycloak outage row; readiness stays UP by design |
| OPS-3 | Low | Unbounded `uri` tag for SPA deep links on `http_server_requests` | **Fixed**: match-patterns for SPA routes |
| OPS-4 | Low | No upstream latency metric | **Fixed**: `console.upstream.duration` timer |
| OPS-5 | Low | Order-list reads bypass the 3 s page budget (worst case about 5 s); a connect timeout is reported as a read timeout | **Fixed**: order lists via fan-out deadline; connect timeout reported as such |
| OPS-6 | Low | Sites probes asset-service on every load, which always gives NOT_AUTHORIZED and inflates the metric | **Fixed**: probe cached 60 s, no token |
| OPS-7 | Low | Rollback wording omits the source-revision annotation; rollback is untested | **Fixed (runbook)**: revert the promotion commit; marked untested |
| OPS-8 | Info | `maxSurge` gives two pods briefly during a rollout (one failed login possible) | **Documented** in runbook |
| OPS-9 | Info | OpenTelemetry "API usage issue" warning at startup, unexplained | **Not investigated**; next action: one run with `io.opentelemetry.usage` FINEST |

After repairs (operations-console 1d65b2b): full Maven suite 50+5 green; Playwright Firefox 15/15 rerun on the repaired build.
