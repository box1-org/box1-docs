# Agent handoff: deployed; stopped in Phase 7 (live input and the ERP VM)

## Work completed
- **Service / platform workstream:** Service 03, fulfillment adapter ([box1-docs#13](https://github.com/box1-org/box1-docs/issues/13)), `frontier` profile.
- **Slice / requirements:** the whole prompt through Phase 5. The ledger has 29 entries: 22 locally_tested, 2 ci_verified, 2 implemented, 3 blocked.
- **Repository and branch:** `box1-org/fulfillment-adapter` `fulfillment-adapter-v1` at `11778f8`.
- **Changed paths (service):** `pom.xml` (Camel Quarkus BOM 3.40.1.1, contracts pin `eef13ea`); `src/main/java/org/box1/fulfillment/**` (erp1, backend, camel, domain, store, messaging, api); `src/main/resources/{application.properties, META-INF/openapi.yaml, db/migration/V1__fulfillment_schema.sql}`; `src/test/java/org/box1/fulfillment/**`; `.tekton/release.yaml` (`security-gates: gate`, write-free API smoke); `README.md`, `docs/architecture.md`, `docs/runbook.md`, `mkdocs.yml`.
- **PRs, all merged with approval on 2026-11-05 (see `evidence/07-release-live.txt`):**
  - [fulfillment-adapter#1](https://github.com/box1-org/fulfillment-adapter/pull/1): the service.
  - [box1-ops-contracts#8](https://github.com/box1-org/box1-ops-contracts/pull/8): DLQ row and database name, adapter-owned. ERP1 is untouched.
  - [box1-gitops#64](https://github.com/box1-org/box1-gitops/pull/64): KafkaTopic `box1.fulfillment.dlq.v1`.
  - [box1-workloads-dev#65](https://github.com/box1-org/box1-workloads-dev/pull/65): database (no Secret in Git) and runtime env.

## Tests and deployment proof
- **Commands and results:**
  - `./mvnw verify -DskipITs=false -Pcontainers`: 123 tests + 5 ITs pass; Checkstyle 0; SpotBugs/FindSecBugs 0 (`evidence/05-after-review.txt`).
  - ERP1: 65 fixtures, 12 names, 3 equivalence pairs, 3 sequences and the mapping pass at `eef13ea`. The sequences also pass through the database-backed consumer.
  - `evidence/scripts/scenarios.py` against the #14 harness (`box1-ops-erp-simulator@c84c910`): 50/50.
  - `evidence/scripts/tui_ship.py`: the real TUI, driven by keystrokes, shipped a request, and the adapter emitted `shipment.confirmed.v1` with the TUI's `shipmentId` (6/6).
- **CI status:** fulfillment-adapter#1 PR pipeline passed on `8f576d5` and `11778f8`. box1-workloads-dev#65 validate and smoke passed. box1-gitops#64 guard and smoke passed (`evidence/06-ci.txt`).
- **GitOps PR and deployed image digest:** box1-workloads-dev#73 (`3668f3b`) promoted `sha256:9247f98fee515d8fad98d9c4665e84c9464dc2be94a02215958b9cc54ec6a931`. Release `fulfillment-adapter-release-kz42z` passed build, the security gate, promote and both smokes. Argo is Synced/Healthy at `3668f3b`, and the pod runs that digest.
- **Routes / endpoints verified (live):** `/api/info` reports `gitRef 0a44cc6`; `/q/health/ready` 200; anonymous POST and reconcile return 401; GET of an unknown ID returns a 404 problem; metrics are exposed. The consumer ignored the two retained `order.placed.v1` events.

## Contract state
- **OpenAPI / event schemas changed:** a new adapter OpenAPI (`META-INF/openapi.yaml`). No event schema changes. `shipment.*` events validate against the pinned envelope and payload schemas, and are compatible with the order and inventory parsers (`evidence/02-contracts.md`).
- **Database migrations and forward compatibility:** a new `V1__fulfillment_schema.sql`. It was edited during review before any deployment. Rollback means restore; untested.
- **Consumer compatibility / pending follow-up:** contracts#8 adds `box1.fulfillment.dlq.v1` to `TOPICS.md`. An adapter OpenAPI in `box1-ops-contracts/openapi/` is optional and not proposed.

## Operations and safety
- **Secrets externalized / auth boundaries:**
  - Database password: a Secret created out of band (D-012).
  - SFTP key and known_hosts: an optional Secret volume (D-007).
  - Writes and `/internal/**` need a box1-realm JWT with audience `fulfillment-adapter` and role `fulfillment-writer`; anonymous gets 401. No Keycloak client exists yet (D-002).
  - Reads are `permit` in dev (D-016).
- **Telemetry evidence:** JSON logs correlate request, upload, ERP result and outcome event by `fulfillmentRequestId`. `traceparent` and `correlationId` travel through ERP1 into the event. The metrics are listed in `docs/runbook.md`. OTel export is off (#22).
- **Resource settings:** adapter 100m / 384Mi request, 1 CPU / 512Mi limit; PostgreSQL 50m / 128Mi, 1 CPU / 512Mi, 5Gi PVC. Not measured on the cluster.
- **Known risks and recovery/rollback:**
  - Merging #1 before its prerequisites would stall the rollout.
  - `earliest` offsets could re-ingest retained events; discovery found none.
  - The rollback procedure is documented but untested.

## Next agent session
- **Next smallest slice:** the Keycloak client (D-002; instructions given to the user), then one live REST fulfillment and its status (it stays QUEUED while SFTP is off). After #25 and D-007: the SFTP Secret, enabling SFTP, the VM round trip and the TUI shipment.
- **Exact files to read:** this file, `checkpoint.md`, `decisions/D-002`, `D-007`, `D-009`, `D-012`, `D-015`, `D-016`, `review-findings/release.md`, `docs/runbook.md`.
- **Blockers and required user decisions:** D-002 (Keycloak client), D-007 (SFTP credential, after the VM exists), D-015 (live input). D-009 and D-012 are resolved.

### What #25 must show to close this run's VM-dependent boxes
- **"The complete round trip works against the ERP VM"**:
  - a reachable, cluster-internal SFTP endpoint for `erpsftp`, with a persistent host key published for the adapter's `known_hosts`;
  - a NetworkPolicy admitting the adapter.
  Evidence: a live `fulfillment.requested.v1` (D-015) reaches the VM's `inbound/`, appears in the TUI, and returns revision 1 `PENDING` to the adapter.
- **"Manual TUI shipment produces the expected modern completion"**: the VM boots into the TUI on its serial console. Ship that request in the TUI; the adapter's status shows `SHIPPED`, and `shipment.confirmed.v1` on `box1.fulfillment.events.v1` carries the TUI's `shipmentId`.

### #14 `docs/VM-INTEGRATION.md` rows this run satisfies
| #14 criterion | Status from this run |
|---|---|
| A request submitted through #13 appears in the ledger | **Shown against the #14 container harness** (REST and Kafka → `inbound/` → ERP ledger), not the VM |
| Manual completion generates a result consumed by the adapter | **Shown against the harness with the real TUI by keystrokes**; adapter status `SHIPPED` and `shipment.confirmed.v1` with the same `shipmentId`. Not the VM serial console |
| Protocol fixtures pass in the Camel adapter | **Satisfied:** every fixture and sequence at `eef13ea` passes in CI (fulfillment-adapter#1) |

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#13
current_phase: 7 (stopped)
repositories:
  - name: box1-org/fulfillment-adapter
    branch: fulfillment-adapter-v1
    commit: 0a44cc6ecd2d852b170bcdf725d946e6901faf32 (main, merge of #1)
  - name: box1-org/box1-ops-contracts
    branch: fulfillment-dlq-v1
    commit: see PR #8 (pins eef13ea for ERP1)
  - name: box1-org/box1-gitops
    branch: fulfillment-dlq-topic
    commit: see PR #64
  - name: box1-org/box1-workloads-dev
    branch: fulfillment-adapter-database
    commit: 1b7dd834919d7d91dbd233499b02296d89cc503c
  - name: box1-org/box1-docs
    branch: agent-run/13-fulfillment-adapter
    commit: see git log
run_state_path: agent-runs/13-fulfillment-adapter/
requirements:
  proposed: 0
  implemented: 1
  locally_tested: 1
  ci_verified: 2
  deployed: 20
  live_verified: 3
  blocked: 2
  superseded: 0
image_digest: sha256:9247f98fee515d8fad98d9c4665e84c9464dc2be94a02215958b9cc54ec6a931
gitops_commit: 3668f3b2400ae49d25dab0ae5e79944e70675720 (box1-workloads-dev)
review_passes_completed: [architecture, persistence, messaging, security, operations, release]
open_decisions: [D-002 Keycloak client, D-007 SFTP credential, D-015 live input]
rollback_state: previous digest sha256:beb87256… (scaffold); rollback is roll-forward or a revert of #73; not exercised
next_action: D-002 decision; then a live REST fulfillment; then #25/D-007 for SFTP and the VM criteria
```
