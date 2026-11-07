# Release pass (phase 5)

Reviewer: a fresh subagent working read-only. It checked CI, `mvnw package` (passes), the live cluster and the box1-workloads-dev manifests. Date: 2026-11-06 EST.

**Conclusion:** the build, promotion, pod start and cluster smoke should pass. In detail:
- **Smoke test:** the gate is the cluster Task `box1-quarkus-smoke`. Its inline checks of greetings, info, health, OpenAPI, the digest and Argo are all untouched by this change.
- **Startup:** the new config has working defaults, so the current ConfigMap starts the pod.
- **Runtime targets:** Keycloak, Kafka, vLLM, the upstreams and the collector all resolve.
- **Memory:** 112Mi of the 512Mi limit is in use.
- **Build:** CI ran 58 tests and 5 ITs. There are no SNAPSHOT dependencies, and Jib is pinned by digest.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| R-1 | medium | None of the prerequisite PRs exist (contracts, Keycloak, workloads). Merging now runs an undeclared consumer group | Open all three PRs, link them from agentic-operations#1, and merge in order only with approval |
| R-2 | medium | The release smoke (`box1-quarkus-smoke`) does not check the new surface: anonymous 401 on `/api/v1/ai/*` and `/mcp`, and the new OpenAPI paths | Recorded as a release-gate gap, because the shared Task is platform-owned and out of scope. Phase 7 checks these by hand, and a follow-up issue covers per-service smoke checks |
| R-3 | low | quarkus-mcp-server 2.0.4 declares Quarkus 3.33.3.1. Compatibility with 3.40.1.1 is shown only by tests | **Repaired in `0cf2604`.** Repair: docs and PR say "tested, not declared compatible" |
| R-4 | low | Rolling update with `maxSurge 1` puts two pods behind the Service, so a GET can miss an analysis and the window is briefly split | Pending: the box1-workloads-dev runtime PR sets `strategy: Recreate` |
| R-5 | low | The PR's "what merging deploys" text is imprecise about what the workloads PR changes | **Repaired** (PR body edited after `0cf2604`): the PR body says the workloads PR is for azp, URLs, resources, strategy and monitoring, and is not needed for startup |
