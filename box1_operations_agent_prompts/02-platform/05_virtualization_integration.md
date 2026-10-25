# Platform 05 — OpenShift Virtualization and legacy ERP coexistence


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** VM-01–06; NFR-04; DEMO-C1/C2

**Dependencies:** ERP simulator service contract and persistent adapter, verified HCO/KubeVirt availability.

## Mission

Demonstrate progressive modernization by moving an unchanged ERP HTTP contract from a container stand-in to an actual VM, when the operator is stable and capacity permits. **The project previously removed a problematic Virtualization namespace; do not recreate/reinstall it as an incidental application step.** Explicitly make `hybrid` profile opt-in.

## Implementation scope and guardrails

- First inspect OCP version, current Virtualization operator/CRDs, required kernel virtualization support, storage class/access mode and memory headroom. If absent, produce GitOps-ready design, compatibility blockers, resource plan and a container-based substitute; do not attempt manual installation in this prompt.
- Proposed VM: minimal CPU/memory and supported RHEL-compatible guest, one persistent disk, network-only ERP HTTP endpoint, restricted service account; use documented supported VM image/boot provisioning method with **no embedded credentials**.
- Start application as OS-managed service (systemd), confirm health, VM power status, disk mount and application logs. Provide a secured route only if explicitly justified; prefer ClusterIP/service bridging to adapter.
- Adapter's `ERP_BASE_URL` points to container or VM; contract/schema/behavioral integration tests must remain identical. Record events during VM outage, bounded retry, recovery and reconciliation.
- Snapshot/backup/restore only if storage/operator capabilities support it; otherwise use application-level backup and document limitations. No claims of live migration or node HA on SNO.
- Optional P2 strangler demo: route a selected business function to modern service behind versioned adapter contract, compare results, rollback safely, and preserve idempotent external effects.

## Verifiable acceptance evidence

- With hybrid enabled and operator supported, status/disk/mount and service health are shown in operator UI.
- Adapter contract tests pass against container and VM without code changes.
- Planned VM stop/restart preserves pending requests, recovers and yields one shipment per fulfillment ID.
- Restore drill produces checksum/record evidence; absence of supported snapshot path is documented accurately.
- On unsupported OCP profile, deliver a clear blocker plus a still-working Core path (no forced install).

## Nominal 64K-context implementation slices

1. Operator/hardware/storage readiness decision record.
2. Guest image/VM manifests and guest provisioning docs (not applied until authorized).
3. Adapter routing and health/observability integration.
4. VM failure/recovery/reconciliation and restore exercise.
5. Optional P2 strangler routing with parity and rollback tests.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
