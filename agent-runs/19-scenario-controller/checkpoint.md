# Checkpoint, run 19 (scenario controller)

- **Updated:** 2026-11-06 13:10 EST
- **Phase:** 6 Delivery. A-1 to A-6 were approved and are done. **Stopped (stop 3):** the Keycloak scope-mapping fix (box1-gitops#79), seeding, role assignment and live runs each need approval (`open-decisions.md`).

## Deployed

| Component | Revision | Live state |
|---|---|---|
| scenario-controller | `f64dee6` (PR #1), image `sha256:a811c457…b269` | `scenario-controller-dev`, Argo Synced and Healthy at workloads `e28c020`, Recreate, 1 pod, ready UP, anonymous 401 |
| inventory-service | `ad472e1` (PR #3), image `sha256:c8b33f7a…7601b` | `inventory-service-dev`, migration V3 applied |
| Keycloak clients | box1-gitops `7d7e0b1` (PR #78) | `inventory-service` ready; `scenario-controller` and `scenario-controller-cli` failing on scope mappings (404). Roles exist. Fix: box1-gitops#79 (open) |
| Secret `scenario-controller-inventory-token` | not in Git | created in `scenario-controller-dev`, key `client-secret`, value never displayed |
| Contract | box1-ops-contracts#10 (open) | not merged |

Evidence: `evidence/08-delivery.md`. Follow-ups: box1-docs#72.

**Ledger:** 1 `live_verified` (VS-ANON), 6 `deployed`, 21 `locally_tested`, 3 `proposed` (LIVE-*), 1 `blocked`.

**Local stack:** the `run19-*` containers and four JVMs are still running. Tear down with `evidence/scripts/stack.sh down`.

## Exact next action

1. **A-4b** (when approved): merge box1-gitops#79 and refresh Argo `keycloak`. Expect both CRs `ready=true`, and operator log SUCCESS for the scope mappings and the service-account role.
2. **A-7** (the user): assign `scenario-operator` and get a token from `scenario-controller-cli`. Check: the catalog read returns 200 with ten titles and gates allowed, and a token without the role gets 403.
3. **A-8** (when approved): `POST /internal/v1/fixtures/seed`, twice; record both responses and the audit.
4. **A-9 to A-11** (each when approved): the live runs. Record the run JSON, the audit and end-state reads in `evidence/09-live-*.md`.
5. Merge box1-ops-contracts#10 when approved.
6. When live proof exists, tick #19's boxes, stating the proof level for each.
