# Service 04 — Legacy ERP simulator (VM-ready workload)


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · VM-01/02; P1 · VM-03/04/05

**Dependencies:** Stable versioned ERP HTTP contract; OpenShift Virtualization is an optional deployment profile.

## Mission and boundary

Deliver a small but plausible **legacy shipment/fulfillment ledger** that can run in a normal container for early testing and inside a small RHEL-compatible VM for the hybrid scenario. Proposed repo: `box1-org/box1-ops-erp-simulator`. No simulated business outcome depends on availability of KubeVirt during Core development.

## Interfaces, domain behavior and implementation constraints

- Versioned contract `POST /api/v1/erp/shipments` with `fulfillmentRequestId`, `orderId`, `sku`, `quantity`, `siteId`, idempotency header; returns stable `shipmentId`, `status`, `shippedAt`. `GET /api/v1/erp/shipments/{fulfillmentRequestId}` supports ambiguous-outcome reconciliation; `GET /health`/actuator equivalent.
- Persist a shipment ledger and processed unique request IDs in a lightweight database or local PostgreSQL as appropriate. A duplicate request returns exactly the original shipment, even after service restart.
- Include controlled test fault API behind demo-only authorization: fixed latency (for SLO alert), temporary 503, forced connection drop *after persistence* (ambiguous acknowledgement), failure reset. Fault modes default disabled in production-like profile.
- Implement runbook for systemd service, OS packages/updates, VM resource request, data disk mount/persistence, health check, logs and safe backups; use a deterministic container deployment when VM capacity/operator compatibility is insufficient.
- Contract should be more important than its packaging: same API works from a container, VM, or future modernized implementation. No privileged cluster access inside VM.

## Acceptance evidence (automate where practical)

- Create shipment twice with same request ID and differing transport timing: one ledger row and stable response.
- Failure-after-commit mode demonstrates adapter GET reconciliation instead of duplicate shipments.
- Stop/start service and VM (when available) preserves ledger; health and metrics reflect outage.
- VM-specific test shows storage attachments and API access only after platform readiness validated.
- Restore drill is documented and does not claim live migration or node HA on SNO.

## Recommended 64K-safe implementation slices

1. Stable ERP HTTP contract + ledger + idempotency tests in container.
2. Controlled fault simulation and metrics.
3. VM install/service scripts and disk/backup documentation.
4. Virtualization integration + fail/recover walkthrough without changing the client contract.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
