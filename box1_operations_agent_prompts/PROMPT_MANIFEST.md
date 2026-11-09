# box1 Operations — prompt manifest

All implementation prompts are standalone Markdown. See `manifest.json` for machine-readable order. Each file is intentionally **far below 64K tokens** because Qwen's configured 64K context also includes tool output, repository contents, history and model output. Use one service prompt per coding session plus the shared contracts; preserve ~6K tokens for safety margin. That sizing is for the default `qwen-64k` profile; the `frontier` profile is defined in `00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

- `02-platform/01_contracts_and_data_foundation.md`
- `01-services/01_order_service.md`
- `01-services/02_inventory_service.md`
- `01-services/04_erp_vm_simulator.md`
- `01-services/03_fulfillment_adapter.md`
- `02-platform/05_virtualization_integration.md`
- `01-services/07_experience_bff.md` (superseded by the console backend in `08_operator_console.md`; reference only)
- `01-services/08_operator_console.md`
- `02-platform/02_observability_stack.md`
- `01-services/09_scenario_controller.md`
- `01-services/05_telemetry_service.md`
- `01-services/06_notification_service.md`
- `02-platform/03_mesh_and_rollouts.md`
- `02-platform/04_trusted_delivery.md`
- `02-platform/07_developer_portal_onboarding.md`
- `02-platform/06_ai_inference_hosting.md`
- `01-services/10_ai_operations.md`

## Golden-path changes for the edge sites (#126)

Run in this order. `02` and `03` may run in parallel with `01`; `04` needs `01` and `02`; `05` needs `01`, `02` and `03`. All five carry a `frontier` section.

- `03-golden-path/01_onboarding_profile_dispatch.md` (#136)
- `03-golden-path/02_gitops_vm_instance_validate_promote.md` (#139)
- `03-golden-path/03_vm_cloud_init_nocloud.md` (#140)
- `03-golden-path/04_artifact_profile_quarkus_monorepo.md` (#137)
- `03-golden-path/05_vm_instance_profile_template.md` (#138)
