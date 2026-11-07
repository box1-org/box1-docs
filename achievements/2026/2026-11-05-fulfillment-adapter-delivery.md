# Fulfillment adapter: durable Camel integration with the legacy ERP, delivered and live

**Date:** 2026-11-05 (America/New_York)

**Status:** Delivered and live in `fulfillment-adapter-dev`. Acceptance is partial: the ERP VM does not exist yet ([#25](https://github.com/box1-org/box1-docs/issues/25)), so SFTP dispatch is off on the cluster. [box1-docs#13](https://github.com/box1-org/box1-docs/issues/13) stays open with 13 of 15 boxes ticked, each with its proof level stated in an issue comment.

This was a `frontier` profile run. Its run state, decisions, evidence, review findings and pilot log are in [`agent-runs/13-fulfillment-adapter/`](../../agent-runs/13-fulfillment-adapter/).

## Outcome

`fulfillment-adapter` is the modern boundary in front of the legacy ERP appliance from [#14](https://github.com/box1-org/box1-docs/issues/14). Apache Camel routes run inside the Quarkus service. They accept fulfillment requests durably, translate them into ERP1 legacy files, exchange those files over SFTP, reconcile the ERP's results and publish `shipment.confirmed.v1` and `shipment.failed.v1`. The adapter never calls the ERP over HTTP.

| Item | Value |
|---|---|
| Release | `box1-ci/fulfillment-adapter-release-kz42z`: build, security gate (`gate`), promote, shared smoke, adapter API smoke all Succeeded |
| Source | `box1-org/fulfillment-adapter` `0a44cc6` |
| Image | `image-registry.openshift-image-registry.svc:5000/box1-ci/fulfillment-adapter@sha256:9247f98fee515d8fad98d9c4665e84c9464dc2be94a02215958b9cc54ec6a931` |
| GitOps | `box1-workloads-dev` `3668f3b` ([#73](https://github.com/box1-org/box1-workloads-dev/pull/73), merged by the pipeline); Argo `fulfillment-adapter` Synced/Healthy |
| Route | `https://fulfillment-adapter-dev.apps.ocp.box1.org` |
| Protocol | ERP1 from `box1-ops-contracts` `eef13ea`, pinned and consumed unchanged |

**What the service does:**
- Kafka `fulfillment.requested.v1` (group `fulfillment`) is the production input. `POST /api/fulfillments` serves demos and operators. Both enter one Camel acceptance route, which commits the request and its dispatch intent before answering.
- Equivalent repeats (ERP1 §6) resolve to the same request. A conflicting reuse gets 409 over REST; on Kafka it is recorded and dead-lettered.
- A custom Camel `DataFormat` implements ERP1 framing: escaping, code-point lengths and the SPEC §3 validation order. Camel Bindy is not used.
- **Dispatch** uploads `.REQ…tmp` and renames it. **Result ingestion** commits each result, plus any outcome event via the outbox, before moving the file to `consumed/`. **Reconciliation** recovers lost uploads and lost results with equivalent resends, bounded, then sets needs-attention.
- Status keeps four facets apart: acceptance, dispatch, ERP acknowledgement and business outcome. `HELD` is never treated as a transport failure.
- Writes and operator actions need a box1-realm token with audience `fulfillment-adapter` and the client role `fulfillment-writer`. SFTP uses a key with strict host-key checking and no accept-new mode.

## Starting baseline

- `fulfillment-adapter` was a Golden Path scaffold (`b23e7dd`) serving greetings at `sha256:beb87256…`.
- **It had no database.** It was onboarded with PostgreSQL off: `postgres.yaml` was empty and no database Secret existed. The prompt had assumed otherwise.
- There was no fulfillment dead-letter topic and no Keycloak client for any service API except asset-service.
- The ERP1 protocol and fixtures were merged in `box1-ops-contracts` (#6). The ERP itself existed only as #14's container harness; no ERP VM existed.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Contracts | [box1-ops-contracts#8](https://github.com/box1-org/box1-ops-contracts/pull/8) | `d21d91f` | `box1.fulfillment.dlq.v1` in `TOPICS.md`; database name mapping. ERP1 untouched |
| Platform | [box1-gitops#64](https://github.com/box1-org/box1-gitops/pull/64) | `0f5ff2d` | KafkaTopic `box1.fulfillment.dlq.v1` (3 partitions, 14 days) |
| Runtime | [box1-workloads-dev#65](https://github.com/box1-org/box1-workloads-dev/pull/65) | `ff2595b` | PostgreSQL (PVC, Deployment, Service, NetworkPolicy) **with no Secret in Git**; adapter env; 384Mi request; optional SFTP Secret volume; SFTP off |
| Service | [fulfillment-adapter#1](https://github.com/box1-org/fulfillment-adapter/pull/1) | `0a44cc6` | Adapter, tests, OpenAPI, runbook, `security-gates: gate`, write-free API smoke |
| Identity | [box1-gitops#69](https://github.com/box1-org/box1-gitops/pull/69) | `60cf703` | Public PKCE Keycloak client `fulfillment-adapter` with role `fulfillment-writer` |

**Made outside Git, by or with the owner's approval:**
- The owner created Secret `fulfillment-adapter-postgres` in `fulfillment-adapter-dev` out of band, before #65 merged.
- A `box1-kafka` Argo sync of the single KafkaTopic `box1.fulfillment.dlq.v1`, with prune off. That Application has no automated sync.
- The owner granted `fulfillment-writer` to `mike` in the Keycloak admin console.

**Decisions with consequences** (records are in the run state's `decisions/`):
- The REST paths follow the issue (`/api/fulfillments`), not the `/api/v1/` convention.
- Callers must supply `fulfillmentRequestId`; the adapter never generates one.
- The adapter never emits `shipment.failed.v1` with `retryable: true`. Transport trouble becomes needs-attention, because the ERP may already have shipped.
- Status reads are open in dev (`FULFILLMENT_READ_POLICY=permit`; IDs and codes only, never operator reason text). Writes always need the role.
- **The database password is a manually created Secret.** It must be preserved in any restore; a managed store is #41.

## Validation and evidence

| Test | Expected | Observed |
|---|---|---|
| Local suite with real PostgreSQL 15 and Kafka 4.2 | Pass | 123 tests + 5 ITs, Checkstyle 0, SpotBugs/FindSecBugs 0 (after review repairs) |
| ERP1 fixtures at `eef13ea` | All pass | 65 files, 12 names, 3 equivalence pairs, 3 sequences, mapping; the sequences also pass through the database-backed consumer. CI-verified |
| Fault scenarios against the #14 ERP harness (`box1-ops-erp-simulator@c84c910`) | Recover or bound | 50/50 checks: held → released → shipped; rejection with code and no text; AUTO from Kafka; SFTP down; changed and unknown host keys; lost upload; lost result; kill -9 before and during upload; needs-attention plus bulk reconcile; real `CONFLICTING_REUSE`; storage down (503); redelivery; hidden names |
| Manual operator completion (harness) | Modern completion | Real TUI keystrokes shipped a request; `shipment.confirmed.v1` carried the TUI's `shipmentId` (6/6) |
| Release `kz42z` | All stages pass | Including the first enforced security gate on this image and the adapter API smoke |
| Running image | Promoted digest | Pod imageID `sha256:9247f98f…`; `/api/info` `gitRef` `0a44cc6` |
| Anonymous write through the Route | 401 | 401 for `POST /api/fulfillments` and for reconcile, by hand and in the release smoke |
| Authenticated write through the Route | 202, durable | The owner's PKCE login → `POST ful_demo1` 202. Status `ACCEPTED`/`QUEUED`/`AWAITING_ERP`; backlog 1; log line carries request, order and trace IDs |
| First consumer start | No stale work | Read the two retained `order.placed.v1` events and ignored them; no dead letters |

Six same-model reviewer passes (architecture, persistence, messaging, security, operations, release) found defects the tests had missed. Two were High:
- ERR-driven resends could loop forever.
- A REST failure would have echoed `Authorization` and a stack trace.

All findings were fixed or recorded with an owner action before release, and the full suite and scenarios were rerun.

**Not tested:**
- Anything involving the ERP VM.
- SFTP from the cluster.
- A Kafka-originated fulfillment on the cluster (no live order was approved).
- Load.
- Rollback.

## Final operational state

- **Argo `fulfillment-adapter`** (automated, no prune) manages the adapter and its PostgreSQL from `box1-workloads-dev`, at digest `9247f98f…`, alongside the existing Route.
- **SFTP is disabled** (`FULFILLMENT_SFTP_ENABLED=false`). Accepted work stays queued: `ful_demo1` is queued and will be the first file uploaded once SFTP is on.
- **Manual resources outside Git:** the database Secret, the KafkaTopic sync, and the role grant.
- **Idle resource use:** 214Mi for the adapter, 33Mi for PostgreSQL.

## Recovery and follow-ups

- **Roll back** by promoting the previous digest or reverting box1-workloads-dev#73. This has not been exercised. The V1 schema is new, so database rollback means restore.
- **Operator procedures** (needs-attention, bulk reconcile, DLQ replay, host-key rotation) are in the service's `docs/runbook.md`.
- **To finish #13**, three things are needed:
  - #25 must provide the VM's internal SFTP endpoint, with a persistent published host key and a NetworkPolicy admitting the adapter.
  - Provision the `fulfillment-adapter-sftp` Secret (decision D-007), then enable SFTP in the workloads.
  - Show a request reaching the VM and returning from a TUI shipment as `shipment.confirmed.v1`.
- **Open:**
  - [fulfillment-adapter#2](https://github.com/box1-org/fulfillment-adapter/pull/2) adds `scripts/operator-login.py`, an operator login helper. CI passed; not merged.
  - A live Kafka-originated fulfillment awaits approval (decision D-015).
  - The run-state branch has not been merged to `main`.
- **Related:** Vault ([#41](https://github.com/box1-org/box1-docs/issues/41)) for the manual Secret, and [#22](https://github.com/box1-org/box1-docs/issues/22) for trace export.
