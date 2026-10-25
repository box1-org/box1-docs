# Quality gates and reproducible acceptance

Map every changed behavior to acceptance evidence. Priority convention: **P0** = mandatory business baseline; **P1** = flagship integrated platform; **P2** = extensions.

## Every service PR

- Code compiles in reproducible Maven/npm commands.
- Unit tests cover happy path, validation errors, missing dependencies, and idempotent duplicate/replay cases as applicable.
- Integration tests with Testcontainers/Dev Services or deterministic stand-ins; no destructive shared-cluster dependency for basic test suite.
- OpenAPI/JSON Schema compatible with shared contracts; consumer-driven tests for async interfaces where practical.
- Structured logs, correlation IDs, OpenTelemetry trace propagation, Micrometer metrics; no secrets or unneeded PII in telemetry.
- Liveness/readiness, external config, bounded retry/backoff, idempotent shutdown, resource requests/limits.
- Clear migration rollback and backup/restore instructions for stateful changes.
- Reuse Golden Path checks, build digest, GitOps PR and Argo CD verification when deployment is actually permitted.

## P0 scenario tests

1. A `POST /api/v1/orders` with the same idempotency key and payload creates **one** order; same key plus changed payload gets a conflict.
2. Concurrent requests for scarce stock allocate **no more than available**.
3. Replaying `order.placed.v1`, `inventory.reserved.v1`, and `fulfillment.requested.v1` leaves one reservation and at most one ERP shipment.
4. Broker outage after order commit leaves an outbox row that publishes after recovery.
5. ERP slowdown raises measurable fulfillment lag; order remains durable; no retry storm.
6. The UI displays time-ordered events and diagnostic IDs without access to the OpenShift console.
7. Fault reset restores seeded state using a documented, non-destructive method.

## SLO experiments: candidate, not promises

On warmed Core profile with AI workload isolated and synthetic **5 req/s**, test order-create p95 under **800 ms**. With healthy deterministic ERP, target **95% fulfilled within 30 s**. For sampled paths, target **≥95% correlation coverage**. For injected ERP slowdown, target alert creation **within two minutes**. Record actual values and lab conditions; if targets fail, update evidence rather than asserting success.

## Explicit limitations

The single-node cluster is not HA; one GPU's 64K context setting doesn't mean unlimited concurrent sessions; local model output is evidence-*interpreting*, not authoritative. Unavailable platform operators/CRDs are blockers, not permission to fabricate manifests with guessed schema.
