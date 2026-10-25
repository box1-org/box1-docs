# box1 Operations — prompt manifest

All implementation prompts are standalone Markdown. See `manifest.json` for machine-readable order. Each file is intentionally **far below 64K tokens** because Qwen's configured 64K context also includes tool output, repository contents, history and model output. Use one service prompt per coding session plus the shared contracts; preserve ~6K tokens for safety margin.

- `02-platform/01_contracts_and_data_foundation.md`
- `01-services/01_order_service.md`
- `01-services/02_inventory_service.md`
- `01-services/03_fulfillment_adapter.md`
- `01-services/07_experience_bff.md`
- `01-services/08_operator_console.md`
- `02-platform/02_observability_stack.md`
- `01-services/09_scenario_controller.md`
- `01-services/04_erp_vm_simulator.md`
- `02-platform/05_virtualization_integration.md`
- `01-services/05_telemetry_service.md`
- `01-services/06_notification_service.md`
- `02-platform/03_mesh_and_rollouts.md`
- `02-platform/04_trusted_delivery.md`
- `02-platform/07_developer_portal_onboarding.md`
- `02-platform/06_ai_inference_hosting.md`
- `01-services/10_ai_operations.md`
