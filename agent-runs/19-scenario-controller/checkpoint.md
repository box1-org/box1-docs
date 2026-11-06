# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 ~16:05 EST
- **Status: closed** at the user's direction ("close out #19"). Four of the eight acceptance boxes were ticked on cluster proof. The other four are deferred to sub-issue **box1-org/box1-docs#83** (ERP Fault Tolerance), each with local proof.

## Final deployed state

| Component | Revision / image | Managed by |
|---|---|---|
| scenario-controller | `a44419e` (docs on top of `f64dee6`), `sha256:af7af89f…` | Argo `scenario-controller` (box1-workloads-dev) |
| operations-console (Demo control) | `ed2c1ac`, `sha256:5ad138dd…` | Argo `operations-console` |
| inventory-service | `ad472e1`, `sha256:c8b33f7a…` | Argo `inventory-service` |
| Keycloak clients | box1-gitops `7d7e0b1`, `3ddc6c3` (#79), `f257bb6` (#81), `8203a7d` (#84) | Argo `keycloak` |
| Secret `scenario-controller-inventory-token` | not in Git; a temporary workaround | box1-docs#72 item 4 |

**Live proof:** evidence/08, 09, 10, 11 and 12. **Ledger:** 13 `live_verified`; see `requirements.yaml`.

## Open elsewhere
- **#83:** the deferred acceptance.
- **#72:** follow-ups, including the token-Secret workaround.
- **#71:** Kafka authentication.
- **box1-ops-contracts#10:** the inventory routes; open, needs a merge.
- **box1-docs#74:** the achievement log; updated, needs a merge.
- **Left in place:** the never-started PipelineRun `operations-console-validate-kplrr` in `box1-ci`, from a Pipelines as Code GitHub 404.
