# Execution plan — independent slices and dependencies

This is the **recommended sequence**, not a requirement that one agent execute everything. Keep each slice small enough to finish within 64K context including tool outputs.

| Slice | Files | First verifiable result |
|---|---|---|
| 0 | Platform `01_contracts_and_data_foundation` | Versioned schemas, Postgres/Kafka resource plan, compatibility tests |
| 1 | Service `01_order_service` | Idempotent POST and transactional outbox |
| 2 | Service `02_inventory_service` | Concurrent reserve, denial and duplicate event handling |
| 3 | Service `03_fulfillment_adapter` | Replay-safe adapter against HTTP ERP stub |
| 4 | Service `07_experience_bff` + `08_operator_console` | Full visible order lifecycle and timeline |
| 5 | Platform `02_observability_stack` | Order ID links logs, trace and metrics |
| 6 | Service `09_scenario_controller` | Deterministic broker/ERP fault and recovery demo |
| 7 | Service `04_erp_vm_simulator` + Platform `05_virtualization` | Same contract moved behind VM endpoint |
| 8 | Services `05_telemetry` + `06_notification` | Sensor alerts and async notification path |
| 9 | Platform `03_mesh_and_rollouts` | Canary/mTLS/fault injection validated |
| 10 | Platform `04_trusted_delivery` | Negative supply-chain gate and digest proof |
| 11 | Platform `06_ai_inference` + Service `10_ai_operations` | Read-only cited incident answer |

**Prerequisite nuance:** Our Golden Path's phases 1–4 are **already validated**; the table is an application build order, not a request to rerun platform installation. Initial demo may use a deterministic ERP container/stub until virtualization becomes safe to enable. Treat heavy platform features as **profiles**: `core`, `delivery`, `operate`, `hybrid`, `ai`.

## Session discipline

Ask the agent to inspect relevant files, implement a single acceptance feature, test, and hand off. For example: **Order-01** idempotent create; **Order-02** state machine; **Order-03** outbox; **Order-04** consumption and timeline; **Order-05** metrics and failure recovery. Resist “build the entire service” in one 64K-window run.

## Handoff checkpoints

Use `05_HANDOFF_TEMPLATE.md` at the end of each session. At the next session, pass only the latest handoff, the focused prompt, shared contracts, and exact changed files. Fresh verification beats stale context.
