# Service 05 — Asset telemetry service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#15](https://github.com/box1-org/box1-docs/issues/15).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not create or expose real credentials. Never assert success without running the validation.

**Priority / requirements:** P0 · FR-06; P1 · OBS-04/05/06

**Dependencies:** Kafka topic `box1.telemetry.events.v1`, an independently owned reading store, the Keycloak `box1` realm for the console login.

## Mission and boundary

Represent connected industrial equipment at multiple sites. This creates a believable high-volume async workload and an independent incident source, not a thin synonym for Kafka. The service also carries its own **load and chaos console**: a basic web page, served from the same pod, that generates telemetry load and starts random, bounded disruption, like a chaos monkey scoped to this service. Proposed repo `box1-org/box1-ops-telemetry`; see the Frontier profile for the repository that actually exists.

The console only disrupts telemetry. Faults in other services (Kafka, order, inventory, ERP) belong to the scenario controller in `09_scenario_controller.md`.

## Interfaces, domain behavior and implementation constraints

- `POST /api/v1/telemetry/readings` internal/authenticated with `{assetId,siteId,metricName,measuredAt,value,unit}`; validation for bounds, allowed metric names, timestamp skew, payload size and rate limiting. Publish `equipment.reading.v1` with documented partitioning and minimal identifiers.
- Store recent readings in owned persistence with bounded retention and a documented partition/cleanup strategy; `GET /api/v1/assets/{assetId}/readings` pagination + time range and `GET /api/v1/alerts`.
- Per-asset/site threshold policies (for example temperature or vibration), severity, deduplication and hysteresis/debounce to avoid alert storms. Emit `equipment.threshold-exceeded.v1` events when alert transitions become active.
- Backpressure: bounded producer queue, retry, DLQ for invalid events, retention and resource quota; avoid unbounded memory growth. Structured logs/traces and metrics for ingestion rate, drops, lag, alert counts, stale assets.
- No hard-coded operator credentials or uncontrolled public ingestion route.

### Load and chaos console

- **Same pod.** A plain HTML, CSS and JavaScript page served as static resources by this Quarkus application. No separate deployment, frontend build toolchain or CDN; it works without internet access. The page calls only this service's own control API.
- **Load.** Configurable sites, assets, metrics, rate per asset and duration. Seeded and deterministic: the same seed reproduces the same reading sequence, and the page shows the seed and can replay it. Generated readings enter the same validation and publication path as real ingestion, never a shortcut around it.
- **Random chaos.** At random intervals, pick from a telemetry-only catalog: bursts, spikes and sustained breaches; values flapping near a threshold (to exercise hysteresis); stale or silent assets; clock skew and out-of-order timestamps; duplicate readings; invalid units, payloads and oversize payloads; and a pause of this service's own Kafka producer. The random choices derive from the run's seed, so a run can be replayed.
- **Deliberate change.** The page shows the namespace and environment in a banner. A run must be explicitly armed and confirmed. Every run has a maximum rate, maximum duration and TTL auto-stop, and concurrent runs are capped; the server enforces these limits, not just the page. One control stops everything. Each run has an audit record with the actor from the token, seed, catalog entries chosen, start, stop and reset. A pod restart never resumes a run silently. The page reports state honestly and shows "unknown" when the backend cannot confirm it.
- **Safety gate.** Chaos is off unless a configuration flag enables it **and** the namespace is on an allowlist. The demo namespace is named by the user, per `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`.
- **Access.** Served over the service's TLS Route. The page and the control API require a Keycloak `box1` realm login with a chaos-operator role, enforced by the backend. The ingestion API is never reachable anonymously through the Route. Keep the Golden Path smoke endpoints working so release smoke passes.
- **Design ethos.** Box1 is "legacy yet modern: retain what works, make change deliberate". Use the box1 identity from `08_operator_console.md`: minimal charcoal and steel monochrome, the cube "1" mark from the brand kit (not a regenerated logo), and a restrained grid motif. Aim for a dense, calm operator screen rather than a game-like dashboard: keyboard operable, reduced motion respected, WCAG-conscious contrast. Live readouts of rate, alerts and producer lag come from the service's own metrics.

## Acceptance evidence (automate where practical)

- Ingest sample burst without duplicate records or unbounded growth; invalid units/payloads rejected.
- Breach and recovery transitions produce one active alert followed by clear; repeated readings don't spam alerts.
- Time-window query returns stable ordering and pagination.
- Simulated broker outage results in bounded queuing and documented discard/retry behavior rather than silent loss.
- Source event IDs and trace IDs appear in telemetry and incident evidence.
- The console is served from the telemetry pod and requires Keycloak login with the chaos role; anonymous requests to the console controls and to ingestion are rejected.
- A seeded load run is reproducible: the same seed gives the same reading sequence.
- Random chaos runs only telemetry-scoped faults, each bounded by rate, duration and TTL, audited, and stoppable with stop-all.
- Chaos is disabled unless explicitly enabled in an allowlisted namespace.
- The console follows the box1 design ethos and passes automated accessibility checks.

## Recommended 64K-safe implementation slices

1. API, schema/validation, deterministic generator and read model.
2. Kafka producer/consumer and bounded retention/backpressure.
3. Threshold engine with hysteresis and alert event contracts.
4. Chaos catalog, bounded run control, audit and safety gate.
5. Console page, Keycloak protection and accessibility checks.
6. Observability, fault tests and integration to operations UI.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** this service, its console page, its contracts, manifests and documentation. Cross-service faults are out of scope (#19). **Background:** the order and inventory pilots' `pilot-log.md` files record lessons worth reading first.

**Discovery must cover (state observed 2026-11-05; verify before relying on it):**

- the repository: `box1-org/asset-service` was created that day through the Golden Path (template 1.1.0) with this issue's mission text as its description, and held only the scaffold. It appears to be this service's repository rather than the proposed `box1-ops-telemetry`; confirm with the user;
- the deployment: namespace `asset-service-dev` was running with Route `asset-service-dev.apps.ocp.box1.org`. `box1-workloads-dev/workloads/asset-service/` includes `postgres.yaml`, from the same template pattern as the database credential issue in [#41](https://github.com/box1-org/box1-docs/issues/41); Kafka bootstrap is configured;
- contracts: `box1-ops-contracts` has `equipment.reading.v1` but no `equipment.threshold-exceeded.v1` schema;
- Kafka: `box1.telemetry.events.v1` exists in `box1-gitops` `platform/kafka/`, with no telemetry dead-letter topic;
- Keycloak: realm `box1` is managed in `box1-gitops/platform/identity/keycloak/realm/`, with clients for Developer Hub and OpenShell only;
- the release smoke task's required public paths, and how the template exposes the service through its Route.

**Design decisions to record before implementation:**

- how the Route keeps ingestion internal: a separate port and Service, or authentication on every path;
- the load path: in-process into the ingestion pipeline, or an HTTP call to itself;
- default and maximum rates that fit the single node, and how they are enforced server-side;
- random number generator and seed format, so load and chaos choices are reproducible;
- the chaos catalog, with bounds for each entry;
- audit storage and retention;
- threshold policy configuration and hysteresis parameters;
- reading retention and partitioning;
- Kafka offset policy on first start;
- the contracts PR for `equipment.threshold-exceeded.v1`;
- the telemetry dead-letter topic, a shared-infrastructure PR that needs approval;
- the Keycloak client and chaos-operator role, a GitOps PR that needs approval;
- the database credential while #41 is open;
- the demo namespace allowlist, which the user names.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | `equipment.threshold-exceeded.v1` and any reading changes reviewed in `box1-ops-contracts` |
| 3 Implementation | Chaos limits enforced server-side; the page has no logic the backend does not check |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs; the Security pass covers the console and Route |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | One seeded load run and one random chaos run on the cluster, with audit, alert and clear evidence, after approval |

**Verification scenarios:** seed replay gives the same sequence; flapping near a threshold gives one alert then one clear; TTL expiry with the browser closed; stop-all mid-run; pod restart mid-run leaves no chaos running; anonymous request; request without the chaos role; chaos enabled in a namespace that is not allowlisted; producer pause gives bounded queueing; rate and duration caps hold against a request that bypasses the page; invalid and oversize payloads rejected; automated accessibility scan; keyboard-only operation.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
