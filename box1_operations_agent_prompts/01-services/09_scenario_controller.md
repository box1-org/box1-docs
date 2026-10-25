# Service 09 — Scenario control / deterministic fixture service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P1 · FR-09, OBS-06, DEMO-A/B/C

**Dependencies:** Demo cluster namespace allowlist, service fault APIs, seed APIs, a restricted operator identity.

## Mission and boundary

Create a **safe demo orchestration API**, not an arbitrary command runner. Proposed repo `box1-org/box1-ops-scenario-control`. Used only in test/demo namespaces, this component seeds repeatable state and applies named, bounded faults with an audit trail.

## Interfaces, domain behavior and implementation constraints

- Declarative catalog of named scenarios: `baseline-order`, `inventory-contention`, `broker-outage`, `erp-slowdown`, `ambiguous-erp-timeout`, `poison-event`, `bad-artifact-gate`. Each specifies prerequisites, fixture IDs, duration, expected observation and reset action.
- `POST /internal/v1/scenarios/{name}/start`, `/stop`, `/reset`, `GET /internal/v1/scenarios` behind admin/operator authorization and explicit namespace/environment allowlist. No arbitrary `exec`, unvalidated shell, unrestricted Kubernetes writes or arbitrary URL fetches.
- For P0 local tests use service-level fault toggles / injected test dependencies rather than requiring cluster-admin powers. For platform-level faults, use pre-approved minimal resource patch permission **only** after compatible support is confirmed.
- Every start creates `scenarioRunId` and stable correlation marker; emit audit record with actor, time, environment, mode, TTL, impact and reset result.
- Automatic TTL-based reset with documented manual recovery if process crashes mid-scenario. Never delete authoritative production data; reset only deterministic seeded demo data.
- Scenario verification should check actual order IDs and business invariants before claiming completion. Build CLI scripts and README so agent can demonstrate without expanding cluster RBAC.

## Acceptance evidence (automate where practical)

- Attempt to run in a non-demo namespace fails closed; unknown scenario name rejected.
- Every named fault has bounded duration, complete audit trail, stop/reset behavior and positive end-state verification.
- ERP slowdown reproduces alert and long-running order without data loss; inventory contention shows one reservation.
- Interrupted orchestration process does not leave a fault permanently enabled beyond TTL.

## Recommended 64K-safe implementation slices

1. Scenario schema/catalog, allowlist, audit and local deterministic modes.
2. ERP and inventory fault control contracts with safeguards.
3. TTL reset and verification probes.
4. Integrate demo runbook, UI action entry point and automated scenario tests.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
