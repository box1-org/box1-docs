# Service 03 — Fulfillment adapter: Camel REST-to-legacy file integration


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#13](https://github.com/box1-org/box1-docs/issues/13).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, Apache Camel through Camel Quarkus extensions, REST/OpenAPI for the adapter's own boundary, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not create or expose real credentials. Never assert success without running the validation.

**Priority / requirements:** P0 · FR-05, DAT-04/05, VM-02; P1 · VM-04

**Dependencies:** `fulfillment.requested.v1`; the ERP1 legacy file protocol and golden fixtures in `box1-ops-contracts/legacy/erp-file/v1/` (from [#14](https://github.com/box1-org/box1-docs/issues/14)); the ERP SFTP endpoint from `02-platform/05_virtualization_integration.md` ([#25](https://github.com/box1-org/box1-docs/issues/25)); Kafka and PostgreSQL.

## Mission and boundary

Protect the legacy ERP from unreliable upstream callers and unreliable transport. This adapter is the modern integration boundary: it owns request acceptance, upload and acknowledgement state, deduplicated external effects, retry bounds and reconciliation. It implements Apache Camel routes **inside this Quarkus application**. "Fulfillment operator" means this application, not a Kubernetes Operator. Do not introduce Camel K, another integration deployment, or a new broker. Implementation repository: `box1-org/fulfillment-adapter`, onboarded through the Golden Path on 2026-11-05.

The legacy ERP exposes **no HTTP business API**. Do not add an HTTP callback to the ERP as a shortcut. Implementing a replacement fulfillment backend is out of scope.

```text
fulfillment.requested.v1 (Kafka) or authenticated REST request
  -> validate and durably accept command -> acceptance response
  -> Camel dispatch route -> ERP1 REQ file -> SFTP upload to inbound/
  -> ERP imports and publishes revision 1 (PENDING), then later revisions
     (HELD, PENDING, SHIPPED or REJECTED), possibly days later
  -> Camel result route reads outbound/ -> persist result + outbox intent
  -> rename to consumed/ -> shipment.confirmed.v1 / shipment.failed.v1
```

## Interfaces, domain behavior and implementation constraints

- **Inputs, one path.** Consume `fulfillment.requested.v1` with consumer group `fulfillment`, and expose `POST /api/fulfillments` and `GET /api/fulfillments/{fulfillmentRequestId}` (retain existing canonical names and schemas where they apply). Both inputs enter the same durable acceptance and idempotency logic; there is never a second fulfillment implementation or dispatch path. Anonymous callers can never create fulfillments through the Route; the authentication mechanism is a design decision.
- **Durable acceptance.** For a new REST request return `202` with the request ID and a `Location` header only after committing the accepted command and dispatch intent. Equivalent repeats resolve to the same resource; conflicting reuse of an ID returns `409`. Equivalence follows ERP1 section 6, so a Kafka and a REST submission of the same request are the same request. Reject acceptance when durable storage is unavailable; never return `202` for work held only in memory. Never hold a request open while the ERP works.
- **Status model.** Report acceptance, upload, ERP acknowledgement and business outcome separately. A completed SFTP rename means *uploaded*; the ERP's revision 1 `PENDING` result means *accepted by the ERP*; an `ERR` file means the ERP did not accept that upload. Map `PENDING`, `HELD`, `SHIPPED` and `REJECTED` explicitly into the modern model.
- **Camel routes.** Named routes for (1) REST and event command acceptance, (2) durable dispatch and SFTP upload, (3) ERP result and error ingestion, (4) reconciliation and controlled retries. Use Camel Quarkus REST and Platform HTTP, Jackson, and FTP/SFTP, managed by the aligned BOM. **Camel Bindy alone cannot read ERP1** (ERP1 section 9): write an ERP1 framing step, such as a custom `DataFormat`, that applies the escaping, code-point lengths, record order and validation order of ERP1 sections 1 and 3. Bindy may map already-split records by type.
- **Persistence.** Use the service's PostgreSQL with the existing outbox and event-publication patterns. Persist dispatch state, attempts, next-attempt time, upload nonces and the selected backend. Camel's in-memory queues, redelivery counters or default idempotent repositories are never the only record of accepted work. Bounded retry with backoff, then an inspectable needs-attention state. Transport uncertainty never becomes a false business rejection; a valid late result is still accepted and reconciled.
- **Contract translation.** Implement ERP1 from `box1-ops-contracts/legacy/erp-file/v1/SPEC.md` and pin the contracts commit you test against; never copy the spec or fixtures. Map `fulfillment.requested.v1` per ERP1 section 8 (`origin` `EVENT`; REST uses `API`); reject a value the protocol cannot carry explicitly rather than truncating it. Keep modern domain objects separate from legacy record models; delimiter handling, legacy codes and exchange paths never leak upstream. Keep existing event names and schemas unless a real business contract change is required.
- **File exchange.** Key-based SFTP with explicit host-key verification. Upload `REQ.<fulfillmentRequestId>.<nonce>.erp1` as `.<name>.tmp` and rename it; generate names, never accept a path from input. Read only ready `RES` and `ERR` names in `outbound/`. Commit each result (or its quarantine record) and its outbox intent **before** renaming the file to `consumed/<name>.<nonce>`, so a crash in between is a harmless redelivery. Quarantine unexpected names on the adapter side and move them to `consumed/` too.
- **Results.** Apply ERP1 section 7's consumer table exactly: keep `(revision, resultId, bytes)` for every result seen; outcomes are apply, duplicate, late (recorded, never regresses state) or quarantine. Pass the fixture `sequences` in `fixtures/manifest.json`.
- **Errors and recovery.** An `ERR` file means the ERP rejected that upload without changing any request; record it, then either resend a corrected request or move the request to needs-attention. When no result arrives within a bounded time, resend an **equivalent** request under a new nonce: the ERP answers an equivalent repeat by republishing its latest result, which is how a lost upload or lost result is recovered. Never send a non-equivalent request under an existing ID.
- **Outcome events.** `SHIPPED` emits `shipment.confirmed.v1`. `REJECTED` emits `shipment.failed.v1` with `retryable: false` and the ERP1 `reasonCode`; `reasonText` never goes into events. Consumers of `box1.fulfillment.events.v1` include order, notification and inventory.
- **Manual ERP operation.** Treat manual and automatic completion identically, and handle pending, held, manually shipped and rejected requests; delayed, repeated or out-of-order results; ERP and SFTP outages; and shipment committed before result publication.
- **Strangler boundary.** Put the backend behind a connector or strategy boundary with only the legacy-file backend enabled. Persist the selected backend at acceptance; routing changes apply only to new requests. Never automatically redirect an uncertain legacy fulfillment to another backend.
- **Observability.** Logs correlate REST request or event, upload, ERP result and domain event by `fulfillmentRequestId`. `traceparent` and `correlationId` travel inside ERP1 records but no span crosses the ERP. Metrics: backlog, oldest unacknowledged upload, retries and resends, `ERR` files by code, late and quarantined results, needs-attention count.

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
- The adapter passes every ERP1 fixture and result sequence in `box1-ops-contracts` at its pinned commit.
- A lost upload or an `ERR` file is detected and resolved by an equivalent resend or needs-attention, never silently dropped.
- Anonymous requests cannot create fulfillments through the Route.

## Recommended 64K-safe implementation slices

1. Durable acceptance (REST and Kafka into one path), persistence and status API.
2. ERP1 framing and mapping, tested against the shared fixtures.
3. Camel dispatch route and SFTP upload against an SFTP test server.
4. Result and error ingestion with the ERP1 consumer table, quarantine and outbox events.
5. Reconciliation by equivalent resend, bounded retries, needs-attention and metrics.
6. Round trip against the ERP VM from #25 and the GitOps proof.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** the adapter and its required test doubles, adapter-owned contracts, manifests and documentation. The ERP application and ERP1 belong to #14 and the VM to #25; a needed change there is a stop condition for this run. **Run order:** #14's ERP1 protocol and fixtures are merged, so this run can start; it may proceed in parallel with #25.

**Decided by the user (2026-11-05):** `fulfillment.requested.v1` from Kafka is the production input and REST serves demos and operators; both use one durable acceptance path. Build in `box1-org/fulfillment-adapter`.

**Decided by #14 and binding here:** ERP1 location, line items (one `LIN` per v1 event), equivalence, result identity and revisions, status and error codes, durability and encoding. Read `agent-runs/14-erp-appliance/decisions/` before designing.

**Discovery must cover (state observed 2026-11-05; verify before relying on it):**

- `box1-ops-contracts`: ERP1 at `legacy/erp-file/v1/` merged in PR #6 (merge commit `eef13ea`), with `SPEC.md`, 66 fixture files and a Node reference parser. `TOPICS.md` lists order, notification and inventory as consumers of `box1.fulfillment.events.v1`;
- `fulfillment-adapter`: created that day from the Golden Path, scaffold only; namespace `fulfillment-adapter-dev` running with a Route at `fulfillment-adapter-dev.apps.ocp.box1.org`; `box1-workloads-dev/workloads/fulfillment-adapter/` includes `postgres.yaml`, from the template pattern behind [#41](https://github.com/box1-org/box1-docs/issues/41);
- `order-service` on `main` as producer of `fulfillment.requested.v1`: it treats `shipment.failed.v1` with `retryable: false` as `EXCEPTION` and with `retryable: true` as a note only;
- the ERP: until #14's repository exists, its code is the #14 run's local repository and container harness (CentOS Stream 10, OpenSSH SFTP chroot). Its `docs/VM-INTEGRATION.md` lists what #13 must show to close #14's VM checkboxes;
- Kafka in `box1-gitops` `platform/kafka/`: `box1.fulfillment.events.v1` exists; order and inventory have dead-letter topics, the adapter does not;
- secret management: no ExternalSecrets, Vault or SealedSecrets CRD; Vault is #41;
- Camel Quarkus extension availability and versions for the template's Quarkus BOM.

**Design decisions to record before implementation:**

- REST path naming: `/api/fulfillments` from the issue against the repository's `/api/v1/` convention;
- REST authentication: Keycloak `box1` realm token with a role, or no Route exposure for the write path. A new Keycloak client is a GitOps PR needing approval;
- request identity for REST callers who supply no `fulfillmentRequestId`;
- the upload timeout and resend schedule, its bound, and when a request enters needs-attention;
- `ERR` handling by code: which errors are fixed and resent, and which go to needs-attention;
- when, if ever, the adapter emits `shipment.failed.v1` with `retryable: true`, given order only notes it;
- SFTP private key and known-hosts provisioning while #41 is open, and host-key rotation coordinated with #25;
- the SFTP test server, and whether any in-cluster test endpoint is allowed before the VM exists;
- the dead-letter topic for the `fulfillment` consumer group, a shared-infrastructure PR needing approval;
- Kafka consumer offset policy on first start, since retained `fulfillment.requested.v1` events may exist;
- retention for `consumed/` files the adapter owns.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | ERP1 consumed unchanged at a pinned merged commit; adapter OpenAPI and any event changes reviewed for order, notification and inventory compatibility |
| 3 Implementation | No in-memory-only record of accepted work; legacy types confined to the translation layer |
| 4 Verification | All ERP1 fixtures and sequences pass; all scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | A real order reaches the ERP VM, is shipped manually in the TUI, and returns as `shipment.confirmed.v1`, as far as #25 allows |

**Verification scenarios (local, real PostgreSQL, Kafka, an SFTP server and the #14 ERP harness):** duplicate REST requests; Kafka redelivery of the same event; REST and Kafka for the same request; conflicting reuse (`409`); anonymous REST request; storage unavailable at acceptance; crash after acceptance commit and before upload; SFTP down, then recovered; upload interrupted before rename; upload lost after rename, recovered by equivalent resend; each `ERR` code the adapter can provoke; host key changed or unknown; result redelivery; out-of-order, late and gapped revisions; every quarantine row of the ERP1 consumer table; held then released then shipped; rejection with a reason code and no reason text in the event; crash between result commit and the rename to `consumed/`; retry exhaustion to needs-attention; adapter restart with pending work; customer data in logs or events.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
