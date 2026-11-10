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

Run in this order. `02` and `03` may run in parallel with `01`; `04` needs `01` and `02`; `05` needs `01`, `02` and `03`; `06` is listed below. All six carry a `frontier` section.

- `03-golden-path/01_onboarding_profile_dispatch.md` (#136)
- `03-golden-path/02_gitops_vm_instance_validate_promote.md` (#139)
- `03-golden-path/03_vm_cloud_init_nocloud.md` (#140)
- `03-golden-path/04_artifact_profile_quarkus_monorepo.md` (#137)
- `03-golden-path/05_vm_instance_profile_template.md` (#138)
- `03-golden-path/06_staged_site_rollout.md` (#141): needs `02` and `05`, and a `site-gateway-os` from `04-edge-sites/01`, so it runs after that prompt

## Edge sites (#126–#133)

Run after the golden-path changes above. `02` and `03` may run in parallel once `01` is delivered; `04` needs `01`–`03`; `06` needs `01` and `02`; `05` needs `02` and `04`; `07` needs `02` and `05`; `08` needs `04` and `03-golden-path/06` (#141); `09` closes the epic. All nine carry a `frontier` section. The Kafka identity parts of `03` and `09` are blocked on #71.

- `04-edge-sites/01_site_foundation.md` (#126: contracts and `site-gateway-os`)
- `04-edge-sites/02_site_forwarder_outbox.md` (#127)
- `04-edge-sites/03_site_machine_identity.md` (#131)
- `04-edge-sites/04_site_status_sites_map.md` (#130)
- `04-edge-sites/05_asset_site_ingestion_stale_alert.md` (#128)
- `04-edge-sites/06_site_pick_lists_reconciliation.md` (#129)
- `04-edge-sites/07_site_otel_collector.md` (#132)
- `04-edge-sites/08_site_greenboot_rollback.md` (#133)
- `04-edge-sites/09_edge_sites_acceptance.md` (#126: NetworkPolicy, runbooks and epic acceptance)
