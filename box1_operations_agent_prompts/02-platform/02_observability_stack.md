# Platform 02 — Full observability and incident evidence


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** OBS-01–07; FR-04/06; NFR-07; DEMO-A2

**Dependencies:** Core order inventory adapter and telemetry instruments; known available monitoring/logging/trace operators.

## Mission

Make a business symptom navigable across metrics, logs, traces, events and deployment history. **Do not duplicate or replace built-in OpenShift monitoring**. Compose a resource-aware OpenTelemetry-compatible pipeline and a repeatable delayed-order incident dashboard.

## Implementation scope and guardrails

- Discover existing OpenShift monitoring/user-workload monitoring and logging/tracing collectors, storage backends, operators/CRDs; record compatibility/cluster resource usage before proposing new deployments. Choice of Prometheus, Loki/Red Hat logging, Tempo/Jaeger/Red Hat tracing must follow available supported stack—**do not assume any specific stack is already installed**.
- End-to-end trace: UI/BFF order POST → order outbox → Kafka → inventory → order consumer → fulfillment adapter → ERP HTTP and acknowledgment. Use W3C `traceparent`; for async delayed processing, represent producer/consumer spans or span links accurately. Ensure order ID and trace ID can be correlated even if sampling misses a span.
- JSON structured logs include bounded fields `service.name`, `environment`, `orderId`, `correlationId`, `traceId`, `eventId`, `errorCode`; redact credentials, customer PII, prompt contents.
- Application/business metrics: order-create latency, oldest unfulfilled order age, inventory rejection count, Kafka consumer lag/DLQ, outbox pending/age, ERP timeout and retry rates, notification backlog, telemetry alert count; keep metric label cardinality safe (never make orderId a Prometheus label).
- SLO dashboards: proposed test targets order API p95 <800ms at 5 req/s with AI idle, 95% fulfillment <30s with healthy simulated ERP, >=95% correlation coverage of sampled order paths, ERP slowdown alert <2 minutes. Test and revise empirically; never call them guaranteed production SLAs.
- Deployment change overlay from Git SHA, immutable image digest, source PR and rollout time; ensure operator can retrieve exact evidence through BFF and incident UI without kubectl permissions.
- Retention, sampling and dashboard refresh tuned to SNO host RAM/storage. Introduce `operate` GitOps profile and make it disableable without destroying Core business state. Define response to observability backend outage (app business flow should continue).

## Verifiable acceptance evidence

- Trace and log query given sample `orderId` reaches at least the order, inventory and adapter boundary; evidence links resolve or explicitly show missing source.
- ERP slowdown triggers defined alert within measured window and a dashboard shows order-age and adapter errors.
- Deployment SHA/digest time can be correlated with simulated regression.
- Structured log audit shows no raw bearer tokens/credentials and no customer personal data.
- Disabling operate profile does not break order POST or fulfillment correctness.

## Nominal 64K-context implementation slices

1. Inventory available observability APIs; write component/budget plan.
2. Instrument/reference distributed tracing and trace-context contract tests.
3. Centralized logs + redaction, sampling and retention.
4. Business metrics, dashboards and alert definitions.
5. One traced fault drill with recorded evidence bundle and resource cost.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
