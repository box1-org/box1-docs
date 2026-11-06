# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 ~01:45 EST
- **Phase:** 3 Implementation, starting. Phases 0 to 2 complete.
- **User answers (2026-11-06):** table accepted (D-004); inventory-service change authorized (inventory-service#3 open, merge needs approval); allowlist delegated (D-006: `scenario-controller-dev`); Kafka issue filed (#71).
- **Still open:** O-3 controller identity (Keycloak clients, secret), O-11 database credential, merges, cluster seeding and runs.
- **Branches:** inventory-service `run19-fixture-admin` `fca04be` (PR #3); scenario-controller `main` `203968e` (untouched so far); run state `agent-run/19-scenario-controller`.
- **Tests:** inventory-service CI set pass; containers set 74 + 10 IT pass (local, 2026-11-06 ~01:15 EST).
- **Design:** D-006 to D-011.

## Exact next action

Implement the controller in `run19-scenario-controller` on branch `run19-controller` per D-008/D-009/D-010: catalog, gates, auth, audit and run tables (Flyway), scenario classes for baseline-order, inventory-contention and the three guided ERP scenarios, TTL scheduler and startup abort, seeding, stardate, CLI script, README/architecture/runbook. Then local verification (Phase 4) against a local stack of order-service, inventory-service (PR #3 head), fulfillment-adapter and the ERP harness, all in `run19-*` containers.
