# Service 03 — Fulfillment adapter: Camel REST-to-legacy file integration


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#13](https://github.com/box1-org/box1-docs/issues/13).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, Apache Camel through Camel Quarkus extensions, REST/OpenAPI for the adapter's own boundary, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not create or expose real credentials. Never assert success without running the validation.

**Priority / requirements:** P0 · FR-05, DAT-04/05, VM-02; P1 · VM-04

**Dependencies:** `fulfillment.requested.v1`; the legacy file protocol and golden fixtures from `04_erp_vm_simulator.md` ([#14](https://github.com/box1-org/box1-docs/issues/14)); the ERP SFTP endpoint from `02-platform/05_virtualization_integration.md` ([#25](https://github.com/box1-org/box1-docs/issues/25)); Kafka and PostgreSQL.

## Mission and boundary

Protect the legacy ERP from unreliable upstream callers and unreliable transport. This adapter is the modern integration boundary: it owns request acceptance, dispatch and acknowledgement state, deduplicated external effects, retry bounds and reconciliation. It implements Apache Camel routes **inside this Quarkus application**. "Fulfillment operator" means this application, not a Kubernetes Operator. Do not introduce Camel K, another integration deployment, or a new broker. Proposed repo `box1-org/box1-ops-fulfillment`.

The legacy ERP exposes **no HTTP business API**. Do not add an HTTP callback to the ERP as a shortcut. Implementing a replacement fulfillment backend is out of scope.

```text
fulfillment.requested.v1 (Kafka) or REST request
  -> validate and durably accept command -> acceptance response
  -> Camel dispatch route -> legacy flat-file records -> SFTP upload
  -> ERP processing, automatic or manual (may wait indefinitely)
  -> SFTP result-consumer route -> persist status + event intent (outbox)
  -> shipment.confirmed.v1 / shipment.failed.v1
```

## Interfaces, domain behavior and implementation constraints

- **Inputs, one path.** Consume `fulfillment.requested.v1`, and expose `POST /api/fulfillments` and `GET /api/fulfillments/{fulfillmentRequestId}` (retain existing canonical names and schemas where they apply). Both inputs enter the same durable acceptance and idempotency logic; there is never a second fulfillment implementation or dispatch path.
- **Durable acceptance.** For a new REST request return `202` with the request ID and a `Location` header only after committing the accepted command and dispatch intent. Equivalent repeats resolve to the same resource; conflicting reuse of an ID returns `409`. Reject acceptance when durable storage is unavailable; never return `202` for work held only in memory. Never hold a request open while the ERP works.
- **Status model.** Report acceptance, delivery or reconciliation state, and business outcome separately. SFTP transfer success means delivered to the legacy interface, not shipped. Explicitly map legacy intermediate states (pending, held) and terminal outcomes (shipped, rejected) into the modern model.
- **Camel routes.** Named routes for (1) REST command acceptance, (2) durable dispatch and SFTP publication, (3) ERP result ingestion, (4) reconciliation and controlled retries. Use Camel Quarkus REST and Platform HTTP, Jackson, Bindy for delimited records, and FTP/SFTP, managed by the aligned BOM.
- **Persistence.** Use the service's PostgreSQL with the existing outbox and event-publication patterns. Persist dispatch state, attempts, next-attempt time and the selected backend. Camel's in-memory queues, redelivery counters or default idempotent repositories are never the only record of accepted work. Bounded retry with backoff, then an inspectable needs-attention state. Transport uncertainty never becomes a false business rejection; a valid late ERP response is still accepted and reconciled.
- **Contract translation.** Use #14's versioned protocol and fixtures. Keep modern domain objects separate from legacy record models; delimiter handling, legacy status codes and ERP paths never leak upstream. Preserve required order fields and line items. Keep existing event names and schemas unless a real business contract change is required.
- **File exchange and security.** Key-based SFTP with explicit host-key verification; credentials through the established secret-management approach. Generate safe filenames; never accept a remote path from input. Upload under temporary names and rename to ready names, validated in integration tests. Consume only complete result files. Persist the response and outbox intent transactionally **before** archiving the remote file, so a crash between commit and archive is safe. Deduplicate and order by stable result ID and per-request revision, never by filename; older responses never regress newer state. Quarantine malformed, conflicting or unrecognized results.
- **Manual ERP operation.** Treat manual and automatic completion identically, and handle pending, held, manually shipped and rejected requests; delayed, repeated or out-of-order responses; ERP and SFTP outages; and shipment committed before response publication.
- **Strangler boundary.** Put the backend behind a connector or strategy boundary with only the legacy-file backend enabled. Persist the selected backend at acceptance; routing changes apply only to new requests. Never automatically redirect an uncertain legacy fulfillment to another backend.
- **Observability.** Logs correlate REST request or event, dispatch, ERP result and domain event by fulfillment request ID; `traceparent` does not cross into the ERP, so correlation there is by ID in the file records. Metrics: backlog, oldest pending age, retries, quarantined results, needs-attention count.

## Acceptance evidence (automate where practical)

- REST acceptance is durable before HTTP 202.
- REST-to-flat-file translation runs through Camel.
- The complete round trip works against the ERP VM.
- Manual TUI shipment produces the expected modern completion.
- Duplicate REST requests and file redelivery create no duplicate shipment.
- Pending or held requests are not mistaken for transport failures.
- Adapter restart preserves accepted work and reconciliation state.
- ERP outage does not lose accepted requests.
- Late or out-of-order results reconcile without regressing state.
- Host-key verification is enabled and tested.
- Logs correlate REST request, dispatch, ERP result and domain event.
- Metrics expose backlog, oldest pending age, retries and quarantined results.

## Recommended 64K-safe implementation slices

1. Durable acceptance (REST and Kafka into one path), persistence and status API.
2. Camel dispatch route with Bindy mapping against #14 fixtures and an SFTP test server.
3. Result ingestion, deduplication, ordering, quarantine and outbox events.
4. Reconciliation, bounded retries, needs-attention state and metrics.
5. Round trip against the ERP VM from #25 and the GitOps proof.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** the adapter and its required test doubles, contracts, manifests and documentation. The ERP application belongs to #14 and the VM to #25; a needed change there is a stop condition for this run. **Run order:** start after #14's protocol specification and fixtures are merged; this run may proceed in parallel with #25. The order pilot and #12's frontier definition record lessons worth reading first.

**Decided by the user (2026-11-05):** `fulfillment.requested.v1` from Kafka is the production input and REST serves demos and operators; both use one durable acceptance path.

**Discovery must cover:**

- whether a fulfillment repository exists, and the name to propose if not. As of 2026-11-05 `box1-ops-fulfillment` did not exist; the order pilot used `order-service`, so the name is a decision for the user;
- `order-service` on `main` as the producer of `fulfillment.requested.v1` and consumer of `shipment.*` events, including its consumer group, dead-letter behavior and state handling;
- `box1-ops-contracts`: `fulfillment.requested.v1` carries a single `sku` and `quantity`; `shipment.confirmed.v1` and `shipment.failed.v1` have no held or pending status; #14's protocol location;
- Kafka topics in `box1-gitops` `platform/kafka/`: `box1.fulfillment.events.v1` exists; any adapter dead-letter topic is a shared-infrastructure PR needing approval;
- secret management: as of 2026-11-05 no ExternalSecrets, Vault or SealedSecrets CRD was installed and Vault is [#41](https://github.com/box1-org/box1-docs/issues/41);
- Camel Quarkus extension availability and versions for the template's Quarkus BOM.

**Design decisions to record before implementation:**

- REST path naming: `/api/fulfillments` from the issue against the repository's `/api/v1/` convention;
- request identity for REST callers, and equivalence rules shared with Kafka input;
- line items against the single-SKU v1 event; a breaking event-contract change is a stop condition;
- how pending and held surface (adapter status API only, unless a contract change is approved) and when `shipment.failed.v1` is emitted with `retryable`;
- SFTP private key and known-hosts provisioning while #41 is open, and host-key rotation coordinated with #25;
- the SFTP test server for local tests, and whether any in-cluster test endpoint is allowed before the VM exists;
- retry bounds, needs-attention entry and exit, and operator reconciliation actions with their authorization;
- Kafka consumer offset policy on first start, since retained `fulfillment.requested.v1` events may exist.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | #14 fixtures consumed unchanged; adapter OpenAPI and any event changes reviewed for order-service compatibility |
| 3 Implementation | No in-memory-only record of accepted work; legacy types confined to the translation layer |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | A real order reaches the ERP VM, is shipped manually in the TUI, and returns as `shipment.confirmed.v1`, as far as #25 allows |

**Verification scenarios (local, real PostgreSQL, Kafka and an SFTP server):** duplicate REST requests; Kafka redelivery of the same event; REST and Kafka for the same request; conflicting reuse (`409`); storage unavailable at acceptance; crash after acceptance commit and before upload; SFTP down, then recovered; upload interrupted mid-file; host key changed or unknown; result redelivery; out-of-order and late revisions; held then shipped; rejection; malformed and conflicting result files to quarantine; crash between result commit and remote archive; retry exhaustion to needs-attention; adapter restart with pending work; customer data in logs or events.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
