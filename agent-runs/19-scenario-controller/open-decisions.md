# Open decisions, run 19 (stop 1, Phase 0 exit)

Reported together, 2026-11-06 ~01:25 EST. Evidence: `evidence/01-mechanism-classification.md` (P-1 to P-8). Each item says what it blocks and what I recommend.

| ID | Decision | Blocks | Recommendation |
|---|---|---|---|
| O-1 | Accept the mechanism classification (D-004) | All design | Accept as written |
| O-2 | **Fixture sites and SKUs cannot be created through inventory-service's API** (P-1). Under D-003, seeding needs an inventory-service change that adds an admin API, which this run cannot push | Seeding; `inventory-contention`; `baseline-order` | An inventory-service change, by its owner, adding an idempotent admin endpoint that creates a site (with status) and a site/SKU stock row, behind `inventory-admin`. Not a Flyway seed, which would bypass "seed through the API" |
| O-3 | **Controller identity.** (a) A `scenario-controller` Keycloak client: confidential with a service account (a new secret) for calling inventory admin; (b) an `inventory-service` client holding `inventory-admin`, which does not exist yet (P-2), with an audience for the controller; (c) the operator-facing roles on the controller, proposed `scenario-operator` and `scenario-viewer` | Seeding, stock reset, any authenticated call | Approve the shape first; each client, audience and secret is a separate approval later |
| O-4 | **`red-alert` needs an asset-service change** (P-5: `azp` pin, browser-login tenant on control paths). Out of scope for this run | `red-alert` | Record `red-alert` as not yet possible from the controller; at most, the controller links to the asset-service console. A machine path is the asset owner's change |
| O-5 | **No ERP on the cluster** (P-3: adapter SFTP disabled, no ERP Service) | Every ERP scenario on the cluster, the "ships and completes" half of `baseline-order`, and the Phase 7 guided-ERP check | Prove the ERP scenarios locally against the harness. Leave the cluster guided-ERP acceptance `blocked` until #13/#25 connect the adapter, unless you plan that sooner |
| O-6 | ERP demo faults are off in the VM (P-4) | `erp-delayed-processing`, `erp-crash-after-commit` on the cluster | Leave off; local proof only. Enabling them is a VM change for #25 |
| O-7 | `broker-outage` and `erp-unavailable` are platform- or VM-level with no approved mechanism or RBAC; Argo selfHeal would undo a VM stop | Those two scenarios | Record both as not yet possible on the cluster for this run; local proof only. No RBAC PR unless you want one |
| O-8 | `poison-event`: the only route is the controller producing a malformed record directly to a shared business topic, which works only because the broker accepts unauthenticated producers (reported to you separately) | `poison-event` on the cluster | Local proof only until the broker has authentication and the controller has a scoped producer identity |
| O-9 | `bad-artifact-gate`: nothing checks signatures (P-8). A guided variant would have an operator open a workloads PR with an outside image and the controller read `box1-gitops-validate`'s failure | `bad-artifact-gate` | Record as not yet possible; the guided variant demonstrates digest pinning, not trust |
| O-10 | The demo namespace/environment allowlist, which you name | Any cluster scenario | Your choice; the controller refuses everything until it is set |
| O-11 | Database credential while #41 is open (D-005; details sent to you directly) | Deployment of the controller's audit store | Your choice: keep the template Secret as disposable lab data (as order-service does), or you create a Secret out of band |
| O-12 | Whether to file a backlog issue for the broker's unauthenticated access, given box1-docs is public | Nothing in this run | Your choice; I recorded only this pointer |

## Independent of these decisions

None that is useful before O-1: you asked to see the classification before design depends on it.
