# Service 04 — Python legacy ERP appliance with console TUI and file-based integration


> **Agent task:** Implement this legacy appliance in `box1-org`. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repository and platform state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the invariants below still apply. Backlog: [box1-docs#14](https://github.com/box1-org/box1-docs/issues/14).

**Mandatory operating constraints:** Python 3, `curses`, SQLite, OpenSSH SFTP and systemd, running natively in a Linux VM guest. This is the stated runtime exception to agent-contract rule 6: the appliance deliberately models a legacy system. The ERP exposes **no REST business API, no OpenAPI document and no native Kafka integration**. Tests, least privilege, pinned artifacts, and PR-reviewed delivery still apply. Deliver one scoped acceptance slice under `qwen-64k`, or this appliance's vertical slice under `frontier`; never the entire backlog. Do not create or expose real credentials. Never assert success without running the validation.

**Priority / requirements:** P0 · VM-01/02; P1 · VM-03/04/05

**Dependencies:** the versioned legacy file protocol and golden fixtures (owned here); the fulfillment adapter in `03_fulfillment_adapter.md` ([#13](https://github.com/box1-org/box1-docs/issues/13)); the VM, boot target, console, storage and SFTP provisioning in `02-platform/05_virtualization_integration.md` ([#25](https://github.com/box1-org/box1-docs/issues/25)).

## Mission and boundary

Build a lightweight, operable legacy ERP for the modernization demonstration. It runs natively inside a Linux VM and boots directly into a terminal user interface, from which an operator can inspect the fulfillment ledger, hold requests, ship or reject them manually, and troubleshoot file exchanges. Modern applications reach it only through the fulfillment adapter, which translates REST and events into flat files over SFTP; responses return as outbound files.

Retain an existing ERP repository if one is established; otherwise the proposed repository is `box1-org/box1-ops-erp-simulator`. A containerized development and test harness is useful but never replaces VM acceptance. Do not run the primary application in a container inside the VM.

```text
Modern caller -> REST/JSON or event -> Fulfillment adapter (Quarkus + Camel)
  -> flat files over SFTP -> Python ERP worker + persistent ledger <- console TUI
```

**#14 owns** the Python application, domain behavior, TUI, worker, application systemd units, protocol specification and fixtures. **#25 owns** the VM, default boot target, console binding, storage, networking and access controls. **#13 owns** the Camel routes and modern boundary.

**Out of scope:** full accounting or inventory ERP, SAP/Oracle emulation, EDI, a browser admin UI, a new broker, arbitrary database editing, and a modern replacement fulfillment backend.

## Interfaces, domain behavior and implementation constraints

- **Layers.** One shared domain and persistence layer (validation, request identity, state transitions, shipment creation, audit records, durable outbound-result intents) used by both a background worker (inbound ingestion, optional automatic fulfillment, outbound publication, recovery) and the console TUI. Neither duplicates business rules. Worker and TUI are separate systemd services: `box1-erp-worker.service` and `box1-erp-tui@.service`. Closing or restarting one never stops the other.
- **TUI.** A searchable, filterable ledger showing request and order IDs, business state, shipment ID, origin, line and site details, last update and outbound publication state. A detail screen shows the original request, state history, operator actions and file references. Keyboard-only at 80x24, resize-safe, ASCII-safe, monochrome, letter or number shortcuts; no mouse, true color, special fonts or desktop.
- **Operator actions.** Hold, Release, Ship, Reject (required reason), Re-emit result (no new shipment), Change processing mode. Ship and Reject require confirmation. No SQL editing, deletion of completed shipments, or shell escape.
- **Modes.** `MANUAL` (default demo profile) imports and publishes but leaves requests pending for an operator. `AUTO` fulfills eligible pending requests, respects holds, and uses exactly the TUI's shipment logic. The mode persists across restarts and is shown prominently.
- **Visibility.** Worker heartbeat and freshness; pending, held, quarantined and pending-output counts; recent failures. Distinguish waiting-for-operator, paused or delayed, stopped or unresponsive worker, and publication failure. The TUI stays usable and marks stale data when the worker is down.
- **Ledger integrity.** Worker and TUI share SQLite locally. Use short transactions, bounded lock waits, uniqueness constraints and state or version checks; never hold a transaction across user input or a file transfer. Shipping atomically persists the shipment, state transition, audit record and outbound-result intent. One shipment per fulfillment request ID; equivalent repeats return the existing result; conflicting reuse is rejected; a manual ship racing an automatic ship still yields one shipment.
- **States and audit.** At least `PENDING`, `HELD`, `SHIPPED`, `REJECTED`, with documented transitions; `SHIPPED` and `REJECTED` are terminal. Business state is separate from file publication state. Every mutation records timestamp, request ID, action, previous and new state, actor type (console operator or worker), and label and reason where applicable. An operator-entered name is an audit label, not authenticated identity; the console is a shared session protected by VM-console access.
- **Legacy file protocol.** Versioned, pipe-delimited files over SFTP, with a written specification and shared golden fixtures. It defines record types, field order, encoding, newlines, required fields, lengths, allowed values, delimiter escaping, request identity and payload equivalence, business status and error codes, file naming, publication, archival and quarantine, and response identity and ordering. One logical request per inbound file; preserve every required field and line item. Responses carry a stable result ID, request ID and a monotonically increasing per-request revision; re-emission preserves identity and content. Write under temporary names and rename to ready names on the same filesystem; consumers ignore incomplete files. Document durability (fsync of file and directory) separately from atomic visibility. Inbound, outbound, archive and quarantine areas are distinct, and the SFTP account cannot reach the database.
- **Recovery and faults.** Unpublished results are recovered from the ledger after restart. Malformed files are quarantined with reasons, with a controlled replay that keeps deduplication. An explicitly enabled demo or test mode supports delayed automatic processing, paused publication, a **one-shot** crash after shipment commit and before publication, and re-emission. Faults are visible, scoped and audited, with no restart loop, no HTTP fault-control API and no unrestricted sudo for the TUI.
- **Console start.** The TUI launches directly on the selected VM console as an unprivileged user, without a shell login or manual command. Boot-to-TUI is required for completion. Coordinate `box1-erp.target`, console selection, mounts and SFTP configuration with #25.

## Acceptance evidence (automate where practical)

- The VM boots directly into the operational TUI.
- A request submitted through #13 appears in the ledger.
- MANUAL mode imports requests without automatically shipping them.
- Hold, release, ship and reject operate on real persisted records.
- Manual and automatic processing use the same domain logic.
- Concurrent or repeated actions produce at most one shipment per request.
- Manual completion generates a result consumed by the adapter.
- Re-emitting a result does not create a new shipment.
- A crash after commit recovers the original shipment and its response.
- TUI disconnect or restart does not interrupt background processing.
- Worker failure is visible without taking down the TUI.
- Reboots preserve ledger, audit history and processing mode.
- Protocol fixtures pass in both the Python ERP and the Camel adapter.
- Backup and restore are demonstrated with application-consistent data.

## Recommended 64K-safe implementation slices

1. Protocol specification, golden fixtures and domain layer with SQLite ledger, identity and concurrency tests.
2. Worker: inbound ingestion, AUTO mode, outbound publication, quarantine and recovery after restart.
3. Console TUI over the domain layer, with 80x24 terminal tests.
4. Demo fault mode, audit views, systemd units and application-consistent backup.
5. VM integration with #25 and the end-to-end walkthrough with #13.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** the ERP application, its protocol specification and fixtures, its systemd units, and its documentation. The VM, image, boot target and cluster manifests belong to #25; Camel routes belong to #13. **Run order:** this run goes first. Its protocol specification and fixtures, merged to `box1-ops-contracts`, unblock the #13 and #25 runs, which may then proceed in parallel.

**Discovery must cover:**

- whether an ERP repository exists, and the name to propose if not. As of 2026-11-05 neither `box1-ops-erp-simulator` nor another ERP repository existed; the order pilot used `order-service`, not the proposed `box1-ops-order`, so the name is a decision for the user;
- `box1-ops-contracts`: `fulfillment.requested.v1` carries a single `sku` and `quantity` and `ful_`-prefixed IDs; `shipment.confirmed.v1` and `shipment.failed.v1` exist; there is no legacy file protocol yet;
- how a non-Quarkus repository gets CI, image or package builds and security gates, since the Golden Path template targets Quarkus. Inspect `box1-templates` and the Pipelines as Code setup before proposing anything;
- what #25 needs from this repository to build a RHEL 10 Image Mode (bootc) guest: artifact form, pinning and install layout.

**Design decisions to record before implementation:**

- protocol location: recommended `box1-ops-contracts` (for example `legacy/erp-file/v1/`), so both the Python ERP and the Camel adapter test against the same fixtures;
- line items against the single-SKU `fulfillment.requested.v1`: how v1 maps to legacy records without silently dropping data. A breaking event-contract change is a stop condition;
- request equivalence: which fields define "same content", and the rejection code for conflicting reuse;
- result ID format, revision rules, and how re-emission and late results are ordered;
- status and error codes, and the reason codes for rejection;
- SQLite settings: journal mode, busy timeout, and the version-check strategy for worker and TUI races;
- durability steps for publication and the crash windows they close;
- demo fault mode: how it is enabled, scoped, audited and made one-shot without HTTP or sudo;
- application artifact packaging and pinning for the guest;
- backup method (SQLite online backup API or `VACUUM INTO`, plus the spool) and where #25 stores it.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 2 Contracts | Protocol specification and golden fixtures merged to the shared location; fixture tests pass in Python; adapter run notified |
| 3 Implementation | Worker and TUI share one domain layer; no business rule exists in only one of them |
| 4 Verification | All scenarios below run in the container harness; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs |
| 6 Delivery | Pinned artifact published through a reviewed path and consumable by #25 |
| 7 Live acceptance | VM criteria proven with #25; anything not yet provable is recorded at its reached level, not ticked |

**Verification scenarios (container harness, real SQLite and OpenSSH SFTP):** manual ship racing automatic ship; repeated and conflicting request IDs; hold then AUTO; release; reject with and without a reason; re-emission; crash after commit then restart; paused publication then resume; delayed processing; malformed, truncated and temporary-name files; quarantine and controlled replay; worker stopped while the TUI is open; TUI restarted while the worker processes; 80x24 rendering and resize under a pseudo-terminal; mode persistence across restart; backup then restore with record checks; SFTP account denied access to the database.

## Agent finish-line checklist

- Add or update the protocol specification, fixtures, tests, systemd units, configuration documentation and runbook.
- Run targeted unit, integration and fixture tests and report real command output. Do not confuse a container harness with the VM appliance.
- Record logs (journald, not the TUI display), health signals, resource proposals and security boundaries.
- Provide PR-ready changes and an exact next handoff if permissions or platform pieces aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
