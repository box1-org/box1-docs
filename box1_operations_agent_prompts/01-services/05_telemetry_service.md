# Service 05 — Asset telemetry service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-06; P1 · OBS-04/05/06

**Dependencies:** Synthetic equipment producer, Kafka topic `box1.telemetry.events.v1`, an independently owned reading store.

## Mission and boundary

Represent connected industrial equipment at multiple sites. Proposed repo `box1-org/box1-ops-telemetry`. This creates a believable high-volume async workload and independent incident source—not a thin synonym for Kafka.

## Interfaces, domain behavior and implementation constraints

- `POST /api/v1/telemetry/readings` internal/authenticated with `{assetId,siteId,metricName,measuredAt,value,unit}`; validation for bounds, allowed metric names, timestamp skew, payload size and rate limiting. Publish `equipment.reading.v1` with documented partitioning and minimal identifiers.
- Store recent readings in owned persistence with bounded retention and a documented partition/cleanup strategy; `GET /api/v1/assets/{assetId}/readings` pagination + time range and `GET /api/v1/alerts`.
- Per-asset/site threshold policies (for example temperature or vibration), severity, deduplication and hysteresis/debounce to avoid alert storms. Emit `equipment.threshold-exceeded.v1` events when alert transitions become active.
- A deterministic simulator seeded with asset names, device clocks, and reproducible sample data; baseline, spike, and sustained-breach patterns. Simulator may be a CLI/fixture job; don't require real IoT hardware.
- Backpressure: bounded producer queue, retry, DLQ for invalid events, retention and resource quota; avoid unbounded memory growth. Structured logs/traces and metrics for ingestion rate, drops, lag, alert counts, stale assets.
- No hard-coded operator credentials or uncontrolled public ingestion route.

## Acceptance evidence (automate where practical)

- Ingest sample burst without duplicate records or unbounded growth; invalid units/payloads rejected.
- Breach and recovery transitions produce one active alert followed by clear; repeated readings don't spam alerts.
- Time-window query returns stable ordering and pagination.
- Simulated broker outage results in bounded queuing and documented discard/retry behavior rather than silent loss.
- Source event IDs and trace IDs appear in telemetry and incident evidence.

## Recommended 64K-safe implementation slices

1. API, schema/validation, deterministic fixture generator and read model.
2. Kafka producer/consumer and bounded retention/backpressure.
3. Threshold engine with hysteresis and alert event contracts.
4. Observability, fault tests and integration to operations UI.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
