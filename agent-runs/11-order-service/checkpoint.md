# Checkpoint: box1-docs#11 Service 01, frontier profile

**Updated:** 2026-11-05 02:40 EST
**Current phase:** 0 Discovery, exit criteria met. Stopped before Phase 1.
**Run branch:** `agent-run/11-order-service` in `box1-docs`. Local worktree: `box1-docs-agent-run-11`.
**Changed files:** only this directory. No service, contracts or GitOps branch, commit or PR exists for this run.
**Tests run:** baselines only, see below. No order behavior is implemented, and every ledger entry is `proposed`, except `ORD-GUARD-DEMO`, which is `blocked`.

## Observed baseline

- `box1-ops-order` does not exist. `order-service` is a Golden Path scaffold at `fba518d`, created 2026-11-05 02:08 EST, with no order behavior: `/api/v1/orders` returns 404.
- Deployed: `order-service` Argo Application Synced/Healthy at `box1-workloads-dev` `b52ec2e`, image `sha256:7c206ee3…aa54`, one pod plus a PostgreSQL 15 pod with a 5Gi `lvms-vg1` PVC. The app has 100m/128Mi requests and 1/512Mi limits, using about 146Mi. PostgreSQL has no requests or limits.
- `orders-service` no longer exists as a repository, namespace or Argo Application.
- Kafka: AMQ Streams 3.2.2, Kafka 4.2.0, Ready, five topics Ready at replication factor 1. Plain listener on 9092, no authentication or authorization, no dead-letter topic. Entity operators watch only `box1-kafka`. `KAFKA_BOOTSTRAP_SERVERS` is unset in the order-service workload.
- The live database credential does not meet `postgres/SECRETS.md` (D-005; specifics are withheld because this repository is public). No NetworkPolicy in the namespace. No secret-management CRDs.
- No OpenTelemetry, Tempo or Loki CRDs. User workload monitoring is off, so a ServiceMonitor would not be scraped.
- Node: 12% CPU and 51% memory in use. Memory requests 49%, limits 136%.
- Contracts `5d44122`: `npm test` 3 of 3 pass and `validate` passes, but they miss a real defect: the OpenAPI `Order` schema rejects every valid order, because `allOf` includes `CreateOrder` with `additionalProperties: false`.
- Scaffold `verify`: passes in CI and locally with `DOCKER_HOST` on the Podman socket (8 unit, 5 integration). The cluster task has no sidecars.
- The release pipeline runs with `security-gates: disabled`.

## Contract gaps to resolve in Phase 1 and 2

- OpenAPI: no `/timeline`, no pagination, no `Location` header, no 200 on idempotent replay, and 404/409 without Problem bodies. No examples, and `validate.mjs` would not check them. Pagination can stay additive: keep the array body and add query parameters and a `Link` header.
- Schemas missing: `inventory.rejected`, `inventory.reservation-expired`, `order.state-changed`, `shipment.failed`. Their fixtures are missing too.
- Fixtures have no `traceparent`.
- `postgres/migrations/orders/V1` lacks `order_state_history` and `idempotency_records`. `MIGRATIONS.md` says these are fixtures, and the service owns its real migrations.
- `TOPICS.md` names no dead-letter topic.
- Database and login names conflict with the template (D-004).

## Open decisions

D-001 target repository, D-002 `box1-workloads-dev` authority, D-003 API authentication, D-004 database names, D-005 live database credential. D-006 records planned defaults.

## Open risks

- Live database credential (D-005).
- Unauthenticated order data on a LAN-resolving Route if D-003 chooses B.
- Merging to the service's `main` starts a build and an auto-merging dev promotion, so a merge deploys with no further review step.
- Greeting endpoints must remain, because the platform smoke task asserts them.

## Evidence

`evidence/00-repositories.txt`, `evidence/01-cluster-baseline.txt`, `evidence/03-local-baselines.txt`. There is deliberately no `evidence/02`: the database credential check is not published, and D-005 says how to repeat it.

## Resume notes

Local tests need:

```sh
export DOCKER_HOST=unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')
export TESTCONTAINERS_RYUK_DISABLED=true
```

Re-verify the baseline before relying on it. `order-service` was created minutes before this run, and the platform repositories changed the same night.

## Exact next action

Get the user's answers to D-001 to D-005. Then begin Phase 1: record the prompt's nine required design decisions in `decisions/`, starting with idempotency scope, using the D-003 answer.
