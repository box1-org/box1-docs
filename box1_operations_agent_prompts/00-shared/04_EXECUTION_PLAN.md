# Execution plan — independent slices and dependencies

This is the **recommended sequence**, not a requirement that one agent execute everything. Under the `qwen-64k` profile, keep each slice small enough to finish within 64K context including tool outputs. Under `frontier`, one run covers one row's prompt, not the whole table.

| Slice | Files | First verifiable result |
|---|---|---|
| 0 | Platform `01_contracts_and_data_foundation` | Versioned schemas, Postgres/Kafka resource plan, compatibility tests |
| 1 | Service `01_order_service` | Idempotent POST and transactional outbox |
| 2 | Service `02_inventory_service` | Concurrent reserve, denial and duplicate event handling |
| 3 | Service `04_erp_vm_simulator`, then `03_fulfillment_adapter` and Platform `05_virtualization` in parallel | Shared legacy file protocol; adapter round trip over SFTP to the boot-to-TUI ERP VM |
| 4 | Service `08_operator_console` (with its console backend; `07` superseded) | Full visible order lifecycle and timeline |
| 5 | Platform `02_observability_stack` | Order ID links logs, trace and metrics |
| 6 | Service `09_scenario_controller` | Deterministic broker/ERP fault and recovery demo |
| 7 | Services `05_telemetry` + `06_notification` | Sensor alerts and async notification path |
| 8 | Platform `03_mesh_and_rollouts` | Canary/mTLS/fault injection validated |
| 9 | Platform `04_trusted_delivery` | Negative supply-chain gate and digest proof |
| 10 | Platform `06_ai_inference` + Service `10_ai_operations` | Read-only cited incident answer |

**Prerequisite nuance:** Our Golden Path's phases 1–4 are **already validated**; the table is an application build order, not a request to rerun platform installation. Development may use the ERP's container harness over SFTP, but ERP acceptance requires the VM appliance; the ERP never exposes HTTP. Treat heavy platform features as **profiles**: `core`, `delivery`, `operate`, `hybrid`, `ai`.

## Session discipline

This section applies to `qwen-64k`. `frontier` runs plan their own slices and follow the phases in `07_FRONTIER_EXECUTION_PROFILE.md`.

Ask the agent to inspect relevant files, implement a single acceptance feature, test, and hand off. For example: **Order-01** idempotent create; **Order-02** state machine; **Order-03** outbox; **Order-04** consumption and timeline; **Order-05** metrics and failure recovery. Resist “build the entire service” in one 64K-window run.

## Handoff checkpoints

Use `05_HANDOFF_TEMPLATE.md` at the end of each session. At the next session, pass only the latest handoff, the focused prompt, shared contracts, and exact changed files. Fresh verification beats stale context.
