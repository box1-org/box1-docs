# Platform 01 — Event contracts, PostgreSQL and Kafka foundation


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** DAT-01–07; PLT-03/06; NFR-03/04/06

**Dependencies:** Initial app service repos, existing storage class and Kafka operator support.

## Mission

Provide the smallest durable data and messaging substrate for the real order lifecycle. Produce versioned OpenAPI/JSON Schemas **before** generating independently drifting consumers. This is a shared platform/application foundation, not a reason to duplicate existing registries or operators.

## Implementation scope and guardrails

- Propose/create `box1-org/box1-ops-contracts` with `events/v1/*.schema.json`, OpenAPI specs, contract fixtures, schema compatibility tests, package version and owned event/topic table. Inspect actual repo existence before creation.
- Kafka design: topics `box1.order.events.v1`, `box1.inventory.events.v1`, `box1.fulfillment.events.v1`, `box1.telemetry.events.v1`, `box1.notification.events.v1`; per-topic retention, DLQ, partition key (`orderId` for order lifecycle), resource quotas and consumer group naming. Support a lower-memory local profile only for code tests; flagship profile remains Kafka if supported.
- PostgreSQL: separate per-service databases or schemas with separate DB users; no cross-service reads/joins. Document storage class, PVC sizing, growth, backup, restore and Flyway migration rules. Do not default to an operator with unverified OCP support; choose the least complex supported form for SNO and document durability limitations.
- Provide idempotent sample `OrderPlaced`, `InventoryReserved`, `FulfillmentRequested`, `ShipmentConfirmed` and equipment reading fixtures plus validation tests. Do not use actual customer PII.
- Schema registry is optional; schemas **in Git** with compatibility tests are required. Document version evolution and replay policies.
- Seed/reset script must be safe: explicitly identifies demo DB/topic and avoids destructive operations on non-demo environments.
- GitOps overlays for `core` and optional `delivery/operate/hybrid/ai`; only create or change resources after reading actual `box1-gitops` structure. Declare secrets as references and give bootstrap guidance, not credentials.

## Verifiable acceptance evidence

- Schema fixtures validate; incompatible field deletions fail compatibility test.
- Two service DB users cannot read/write each other's schemas (negative test).
- Kafka message redelivery is demonstrable and tracked; DLQ and replay procedure documented with audit.
- Outbox + crash-before-publish experiment retains business state and eventually emits needed event.
- Postgres restore from seeded backup reproduces expected order/stock records with known checksum; requirements for regular production backups explicitly separate from lab demonstration.

## Nominal 64K-context implementation slices

1. Shared contracts repo and CI schema/OpenAPI validation only.
2. DB ownership/migration/storage proposal and local compose/Dev Services for testing.
3. Kafka topic/consumer/retention/dead-letter manifests for *verified* installation.
4. Backup/replay/restore drill with evidence and selective GitOps PR.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
