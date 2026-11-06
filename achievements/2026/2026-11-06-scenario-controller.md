# Scenario controller: built, reviewed and deployed under the frontier profile

**Date:** 2026-11-06 (America/New_York)
**Status:** Deployed, with operator access live-verified. No scenario has run on the cluster yet. Seeding and the three live runs each await approval. [box1-docs#19](https://github.com/box1-org/box1-docs/issues/19) stays open, with no acceptance box ticked. Full run state, decisions and evidence are on branch [`agent-run/19-scenario-controller`](https://github.com/box1-org/box1-docs/tree/agent-run/19-scenario-controller/agent-runs/19-scenario-controller).

## Outcome

`scenario-controller` runs named demo scenarios against the Box1 order flow with the Starfleet Feline Supply fixture set, and verifies each scenario's outcome before reporting success. It is live in `scenario-controller-dev`, delivered by the Golden Path pipeline with the security gate set to `gate`. Operators reach it with a Keycloak token from the new `scenario-controller-cli` client.

```text
image   image-registry.openshift-image-registry.svc:5000/box1-ci/scenario-controller@sha256:a811c457b88269f22381f63dac1b31d7b25efa93f43a479891a02c65bd2bb269
source  box1-org/scenario-controller f64dee6
gitops  box1-org/box1-workloads-dev e28c020 (Argo CD Synced/Healthy)
```

The catalog holds ten scenarios. Five are available:
- Make it so
- The Trouble with Tribbles
- three guided ERP scenarios, where an operator acts at the ERP console and the controller verifies the result: Hold that order, Number One; Impulse power only; Warp core breach

The other five are recorded as not yet possible, each with its reason and with no code behind it. The controller never adds a fault API to another service. It changes data only through each service's own API, and only additively.

## Starting baseline

- `scenario-controller` had been onboarded through Developer Hub and ran only the Golden Path scaffold (`203968e`).
- inventory-service could not create sites or stock records through its API. Its `/internal/v1` routes required `inventory-admin`, and no Keycloak client could issue that role ([inventory log](2026-11-05-inventory-service.md), D-010).
- asset-service accepts only its own `azp`, chaos injection is disabled on the cluster, and the ERP VM image ships with `[demo] faults=false`.
- At the start, no ERP was reachable from the cluster. A parallel change, box1-workloads-dev#100, connected the fulfillment adapter to the ERP VM over SFTP during the run, which made a live guided-ERP scenario possible.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `inventory-service` | [#3](https://github.com/box1-org/inventory-service/pull/3) | `ad472e1` | Create-once `PUT /internal/v1/sites/{siteId}` and `PUT /internal/v1/stock/{siteId}/{sku}`: 201 created, 200 unchanged, 409 different, 404 unknown site. Migration V3, which is additive. Merged by the user |
| `box1-workloads-dev` | [#106](https://github.com/box1-org/box1-workloads-dev/pull/106) | auto | inventory-service promotion (`sha256:c8b33f7a…`) |
| `scenario-controller` | [#1](https://github.com/box1-org/scenario-controller/pull/1) | `f64dee6` | The controller, its tests, CLI, runbook and architecture docs; release gate set to `gate` |
| `box1-workloads-dev` | [#107](https://github.com/box1-org/box1-workloads-dev/pull/107) | `bd24fe1` | Promotion, opened and merged by the release pipeline |
| `box1-gitops` | [#78](https://github.com/box1-org/box1-gitops/pull/78) | `7d7e0b1` | KeycloakClients `inventory-service` (holds `inventory-admin`), `scenario-controller` (confidential; service account with `inventory-admin`; roles `scenario-viewer` and `scenario-operator`), and `scenario-controller-cli` (public, PKCE, device grant) |
| `box1-gitops` | [#79](https://github.com/box1-org/box1-gitops/pull/79) | `3ddc6c3` (by the user) | Fix: client scope mappings named by internal client ID (below) |
| `box1-workloads-dev` | [#103](https://github.com/box1-org/box1-workloads-dev/pull/103) | `e28c020` | Runtime env: the three gates, upstream URLs, host allowlist, allowed `azp`, token Secret reference, `strategy: Recreate` |
| `box1-ops-contracts` | [#10](https://github.com/box1-org/box1-ops-contracts/pull/10) | **open** | The two inventory routes in the OpenAPI contract |

**Decisions with consequences** (one record each in `decisions/` on the run branch):

- **Mechanism per scenario (D-004, accepted by the user before design).** Each scenario is classified by how it works:
  - *Service API*: Make it so, The Trouble with Tribbles. Red alert also belongs here but is not yet possible, because asset-service accepts only its own `azp`.
  - *Guided ERP*: hold, delay, crash. An operator performs the step at the ERP console, and the controller verifies the outcome through the adapter and order timeline. A step not performed times out as NOT_VERIFIED.
  - *VM level* (ERP unavailable) and *platform* (broker outage, poison event, bad artifact): not yet possible. They would need Kubernetes RBAC or shared-component outages that weren't approved.
- **Three gates (D-008).** Every action is refused and audited unless all three pass:
  - control is enabled;
  - the pod's own namespace, read from the downward API, is on the allowlist (`scenario-controller-dev`);
  - every upstream and token URL is on a host allowlist.

  The controller has no Kubernetes permissions, runs no processes, and has no arbitrary URL fetch.
- **Bounded runs (D-008).** One run at a time, enforced by a unique partial index. Each run has a TTL. Runs abandoned by a dead process are aborted and reset at startup and by a 5-second sweep. Resets are additive restocks keyed for idempotency. The audit trail is append-only, enforced by a trigger, and kept for 90 days.
- **Identity (D-009).** The controller's tokens must have audience `scenario-controller`. Roles count only from `resource_access.scenario-controller`, and only when `azp` is `scenario-controller-cli`. The catalog requires `scenario-viewer`; start, stop, reset and seed require `scenario-operator`.
- **Fixtures (D-007).** Seeding creates four sites and 22 stock records through inventory's create-once routes. Customers and SKUs are plain IDs (`cust_picard`, `CAT-SPOT-BOWL`). Starfleet names and titles are display text only.

## Validation and evidence

| Check | Result | Proof level |
|---|---|---|
| Controller test suite | 48 tests plus 5 packaged integration tests with real PostgreSQL 15. Checkstyle 0, SpotBugs 0. Rerun after review repairs | Local |
| inventory-service test suite | 74 tests plus 10 integration tests | Local |
| End to end against the real order, inventory and fulfillment services, the ERP harness and Keycloak | 37 of 37 checks. They covered:<br>• seeding twice, with no change the second time<br>• the tribble race twice, exactly one reservation each time<br>• hold and release<br>• a 90-second ERP delay<br>• a real crash after commit<br>• a guided step not performed, which timed out as NOT_VERIFIED<br>• SIGKILL mid-run past its TTL, with recovery and reset on restart<br>• anonymous and role-less requests, and an unknown scenario<br>• no data changed outside the fixtures<br><br>Rerun on a fresh stack after the review repairs ([evidence/07](https://github.com/box1-org/box1-docs/blob/agent-run/19-scenario-controller/agent-runs/19-scenario-controller/evidence/07-local-e2e-after-review.txt)) | Local |
| CI | `scenario-controller-validate-std6t` and `inventory-service-validate-8hlzm` Succeeded | CI |
| Five reviewer passes (architecture, persistence, messaging, security, operations), then a release pass | 57 findings, none high; 13 medium. All fixed or recorded ([outcomes](https://github.com/box1-org/box1-docs/blob/agent-run/19-scenario-controller/agent-runs/19-scenario-controller/review-findings/outcomes.md)). The release pass confirmed every merge, digest and Argo state ([release review](https://github.com/box1-org/box1-docs/blob/agent-run/19-scenario-controller/agent-runs/19-scenario-controller/review-findings/release.md)) | Review |
| Releases `scenario-controller-release-v9qm4` and `inventory-service-release-fblwj` | Build, gate, promote and smoke all Succeeded. inventory migration V3 applied. The deployed digests match the release results | Cluster |
| Running controller, final pod | Readiness UP (database). Catalog, runs and audit return 401 to anonymous and malformed-token requests. OpenAPI 200. Flyway at version 2 | Live |
| Operator access | Device login with PKCE through `scenario-controller-cli`. The token carries `azp=scenario-controller-cli`, `aud=scenario-controller` and `scenario-operator`. The catalog returns 200 with all ten titles and plain IDs; fixtures 200; runs empty | Live |

**About the security gate.** `gate` mode enforces RHACS build policies, not vulnerability counts. Both images passed with 0 critical and 10 high findings, the same counts for both, likely from the shared base image.

**Not established live:**
- Seeding, and whether the controller's service-account token carries `inventory-admin`. Seeding will show it.
- Any scenario run on the cluster, including a guided ERP step at the real VM console.
- A role-less user's 403 on the cluster.
- A pod restart mid-run on the cluster.

Most useful repairs found by verification and review:

- **"Shipped exactly once" could never fail.** A duplicate shipment is recorded as a timeline note, and one shipment produces both SHIPPED and COMPLETED. The check now waits a settle window, then counts distinct `shipment.confirmed.v1` event IDs and requires a stable shipment ID.
- **The crash scenario could pass without a crash.** The controller cannot observe the ERP's worker. It now requires two audited operator confirmations, crash armed and crash observed, and reports NOT_VERIFIED without them.
- **A rolling update could let the new pod abort the old pod's live run.** Fixed with `strategy: Recreate`.
- **Over-restocking could make the tribble race fail forever.** Contention now orders all available stock, and reset waits until the run's orders are decided.
- **Keycloak scope mappings failed with 404 after #78 merged.** The RH-SSO operator's scope-mapping call needs the target client's internal UUID, not its clientId. #79 pins the two target clients to the UUIDs Keycloak had already generated and names them in the mappings. Local testing had built the realm through the admin API rather than the operator's CRs, so it never exercised this path.

## Final operational state

- **Argo CD:**
  - manages `scenario-controller` from `box1-workloads-dev` main at `e28c020`, automated with self-heal, `PruneLast`;
  - manages the Keycloak clients from `box1-gitops` (app `keycloak`, automated, self-heal, prune off). All three clients report ready.
  - manages `inventory-service` at its promotion from #106.
- **Data:** no scenario run exists, and fixtures have not been seeded on the cluster.
- **Temporary workaround:** Secret `scenario-controller-inventory-token` in `scenario-controller-dev` was copied by hand, with approval, from the operator-generated `keycloak-client-secret-scenario-controller`. It isn't in Git, and the Deployment references it as optional. If Keycloak rotates the secret, seeding fails until the Secret is recopied. Tracked in [#72](https://github.com/box1-org/box1-docs/issues/72), item 4.
- **Database credential:** the controller uses the template's database Secret arrangement, the same as order-service and inventory-service ([#41](https://github.com/box1-org/box1-docs/issues/41)).

## Recovery and follow-ups

- **Rollback (not exercised).** Revert `box1-workloads-dev` `e28c020` and `bd24fe1` to return to the scaffold image (`175401a5…`), which ignores the controller's V1 and V2 tables. Self-heal undoes a manual `oc rollout undo`.
  - To remove the Keycloak clients: revert the box1-gitops merges. Prune is off on `keycloak`, so the KeycloakClients must also be deleted by hand.
  - Delete the token Secret.
  - The inventory V3 migration is forward-only; older images ignore its rows.
- **Operations:** the controller's [runbook](https://github.com/box1-org/scenario-controller/blob/main/docs/runbook.md) covers the gates, the CLI, abandoned-run recovery, guided-step resets, backup and migration rollback.
- **Device login:** `scenario-controller-cli` requires PKCE (`code_challenge` with `S256`) on the device authorization request, and `code_verifier` on the token request.
- **Awaiting approval, in #19:**
  - cluster seeding;
  - live runs of The Trouble with Tribbles, Make it so, and Hold that order, Number One (the user performs the ERP console steps);
  - merging box1-ops-contracts#10.
- **Follow-ups in [#72](https://github.com/box1-org/box1-docs/issues/72):**
  - ERP-side expiry for demo faults and holds;
  - a fixture-only inventory role narrower than `inventory-admin`;
  - rate limiting for audited refusals;
  - a managed source for the token Secret.
- **Related:**
  - Kafka has no authentication or ACLs ([#71](https://github.com/box1-org/box1-docs/issues/71)).
  - The operations console ([#18](https://github.com/box1-org/box1-docs/issues/18)) must forward a token with audience `scenario-controller` before it can show the catalog. That audience change needs approval.
