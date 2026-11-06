# Service 09 — Scenario control / deterministic fixture service


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#19](https://github.com/box1-org/box1-docs/issues/19).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P1 · FR-09, OBS-06, DEMO-A/B/C

**Dependencies:** Demo cluster namespace allowlist, service fault APIs, seed APIs, a restricted operator identity.

## Mission and boundary

Create a **safe demo orchestration API**, not an arbitrary command runner. Proposed repo `box1-org/box1-ops-scenario-control`. Used only in test/demo namespaces, this component seeds repeatable state and applies named, bounded faults with an audit trail.

It also owns Box1's **canonical demo fixture set**, "Starfleet Feline Supply" (user decision, 2026-11-06): the Federation's premier purveyor of cat accessories, staffed by famous captains with very particular cats. The whimsy is deliberate and contained: it lives in names, titles and descriptions, while identifiers, errors and audit records stay plain and machine-checkable.

## Fixture set: Starfleet Feline Supply

All fixtures are synthetic. IDs match the `box1-ops-contracts` patterns and never change; display names and titles may be tuned.

**Sites** (additive to the inventory service's existing lab seed `site_nyc`, `site_bos`, `site_closed`, which tests rely on):

| `siteId` | Display name | Status | Notes |
|---|---|---|---|
| `site_spacedock` | Earth Spacedock | `ACTIVE` | Main depot; deep stock |
| `site_ds9` | Deep Space Nine, Promenade outlet | `ACTIVE` | Holds the last tribble |
| `site_utopia_planitia` | Utopia Planitia Fleet Yards | `ACTIVE` | Bulk stock |
| `site_neutral_zone` | Neutral Zone outpost | `UNAVAILABLE` | Do not cross. Orders here are rejected |

**Customers:**

| `customerId` | Display name | Habit |
|---|---|---|
| `cust_picard` | Captain Picard, USS Enterprise-D | Orders with quiet authority |
| `cust_data` | Lt. Cmdr. Data | Devoted keeper of Spot; orders precisely one of everything |
| `cust_janeway` | Captain Janeway, USS Voyager | Long-distance orders, very patient |
| `cust_sisko` | Captain Sisko, Deep Space Nine | Shops locally on the Promenade |
| `cust_kirk` | Captain Kirk | Orders tribbles; regrets it |

**Cat accessories** (SKUs):

| `sku` | Product |
|---|---|
| `CAT-SPOT-BOWL` | Spot's Feline Supplement bowl |
| `CAT-PHASER-LASER` | Phaser laser pointer, stun setting only |
| `CAT-TRIBBLE-TOY` | Tribble plush. Purrs. Does not multiply (we checked) |
| `CAT-JEFFERIES-TUNNEL` | Jefferies Tube crinkle tunnel |
| `CAT-HOLODECK-POST` | Holodeck scratching post, safeties engaged |
| `CAT-CAPTAINS-BED` | Captain's chair cat bed |
| `CAT-COMBADGE-COLLAR` | Combadge collar that chirps |
| `CAT-REPLICATOR-FEEDER` | Replicator kibble dispenser |
| `CAT-DILITHIUM-NIP` | Dilithium catnip crystals |

**Telemetry assets:** `asset_replicator_spacedock` (temperature) and `asset_litterbox_transporter_ds9` (vibration).

**Whimsy rules:**

- No franchise logos, images or quoted dialogue beyond short names and titles. The box1 visual identity (`08_operator_console.md`) is unchanged.
- Errors and refusals are plain: "Scenario `erp-unavailable` is not allowed in namespace `x`", not a joke.
- Each audit record shows a computed stardate beside the ISO 8601 timestamp, for display only; the timestamp is authoritative.

**Seeding and reset:**

- Seed only through each service's own API. Seeding is idempotent: running it twice gives the same state.
- Order fixtures use run-scoped idempotency keys `stardock-<scenarioRunId>-<n>`, so a repeat replays the same order.
- Orders cannot be deleted or cancelled through any v1 endpoint. Fixtures are therefore additive and never deleted; a fresh demo uses a fresh run. Reset restores stock and fault state for fixture sites and SKUs only, and touches nothing outside the fixture set.

## Interfaces, domain behavior and implementation constraints

- **Declarative catalog of named scenarios.** Each scenario specifies prerequisites, fixture IDs, duration, expected observation, reset action, its fault mechanism and a display title:

| Scenario | Title | Story |
|---|---|---|
| `baseline-order` | Make it so | Picard orders Spot's bowl from Spacedock; it ships and completes |
| `inventory-contention` | The Trouble with Tribbles | Kirk and Sisko order the last `CAT-TRIBBLE-TOY` at DS9 at once; exactly one reservation wins |
| `broker-outage` | Subspace interference | Kafka unavailable; orders wait and recover without loss |
| `erp-manual-hold` | Hold that order, Number One | The request is held in the ERP console, then released |
| `erp-delayed-processing` | Impulse power only | ERP AUTO processing is delayed; the order waits visibly |
| `erp-crash-after-commit` | Warp core breach (one-shot, contained) | The ERP crashes once after committing a shipment and recovers it |
| `erp-unavailable` | The ERP has cloaked | The ERP VM is unavailable; requests are accepted and delivered later |
| `poison-event` | Q was here | A malformed event reaches a consumer and lands in its dead-letter topic |
| `bad-artifact-gate` | Unsigned shuttlecraft denied docking | An untrusted artifact is refused by the release gate |
| `red-alert` | Red alert | Telemetry load and chaos at Spacedock and DS9 through the asset service's control API |

- **Fault mechanisms.** Use each service's own control surface; never duplicate or bypass it.
  - Telemetry load and telemetry-scoped chaos live in `05_telemetry_service.md`; `red-alert` calls that service's control API, including its stop-all.
  - ERP faults use the appliance's own demo mode (`04_erp_vm_simulator.md`). That mode is switched from the ERP console and there is no ERP HTTP fault API. ERP scenarios are therefore **guided** (the controller states the operator's console step, waits, and verifies the outcome) or **VM-level** (stopping the VM, a platform fault). Never add a fault API to the ERP.
  - Inventory and order behavior come from real requests with fixture data, not hidden switches.
- `POST /internal/v1/scenarios/{name}/start`, `/stop`, `/reset`, `GET /internal/v1/scenarios` behind admin/operator authorization and explicit namespace/environment allowlist. No arbitrary `exec`, unvalidated shell, unrestricted Kubernetes writes or arbitrary URL fetches.
- For P0 local tests use service-level fault toggles / injected test dependencies rather than requiring cluster-admin powers. For platform-level faults, use pre-approved minimal resource patch permission **only** after compatible support is confirmed.
- Every start creates `scenarioRunId` and stable correlation marker; emit audit record with actor, time, environment, mode, TTL, impact and reset result.
- Automatic TTL-based reset with documented manual recovery if process crashes mid-scenario. Never delete authoritative production data; reset only deterministic seeded demo data.
- Scenario verification should check actual order IDs and business invariants before claiming completion. Build CLI scripts and README so agent can demonstrate without expanding cluster RBAC.

## Acceptance evidence (automate where practical)

- Attempt to run in a non-demo namespace fails closed; unknown scenario name rejected.
- Every named fault has bounded duration, complete audit trail, stop/reset behavior and positive end-state verification.
- ERP delayed processing or a manual hold reproduces alert and long-running order without data loss; inventory contention shows one reservation.
- Interrupted orchestration process does not leave a fault permanently enabled beyond TTL.
- The Starfleet Feline Supply fixtures seed idempotently through service APIs: seeding twice gives the same state, and nothing outside the fixture set is changed or deleted.
- "The Trouble with Tribbles" ends with exactly one reservation for the last tribble and one rejected order.
- Guided ERP scenarios state the operator's console step and verify the result before reporting success; a step not performed times out and is reported as not verified.
- Every scenario shows its display title, while IDs, errors and audit fields stay plain.

## Recommended 64K-safe implementation slices

1. Scenario schema/catalog, allowlist, audit and local deterministic modes.
2. Fixture seeding and the "Make it so" and "Trouble with Tribbles" scenarios.
3. ERP and inventory fault control contracts with safeguards. ERP faults use the appliance's own demo mode (`04_erp_vm_simulator.md`); there is no ERP HTTP fault API, so how the controller triggers them is a design decision.
4. TTL reset and verification probes.
5. Integrate demo runbook, UI action entry point and automated scenario tests.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** this controller, its catalog, the fixture set, its contracts, manifests and documentation. Changes to any other service are out of scope; a needed change there is a stop condition. The console's button for starting scenarios is #18's work. **Background:** the earlier pilots' `pilot-log.md` files; the telemetry run (#15) set the bounded, audited fault-control pattern this controller generalizes.

**Discovery must cover (state observed 2026-11-06 America/New_York; verify before relying on it):**

- the repository: no scenario-controller repository existed. Onboarding one through the Golden Path is an approval-required action for the user; confirm its name;
- identifier patterns in `box1-ops-contracts`: `cust_`, `site_`, `ord_`, `res_`, `asset_` followed by `[A-Za-z0-9_-]`; `sku` is free text up to 80 characters;
- inventory: the lab seed `V2__seed_lab_fixture.sql` in `inventory-service` holds `site_nyc`, `site_bos`, `site_closed` and SKUs `SKU-42`, `SKU-7`, `SKU-LAST`. The service has `POST /internal/v1/stock/{siteId}/{sku}/restock`; whether that can create a new site is **not established**. If it cannot, seeding the fixture sites needs an inventory-service change;
- orders: the order service has no delete or cancel endpoint and no API authentication ([#40](https://github.com/box1-org/box1-docs/issues/40)). The operator console run (#18, decision D-011) already uses additive fixtures with run-scoped keys and its own customers `cust_demo_ada`, `cust_demo_lin`, `cust_demo_kai`;
- the ERP: demo faults in `box1-ops-erp-simulator` (`docs/DESIGN.md`: pause publication, delay AUTO, one-shot crash after the next shipment commit) are enabled only by `faults = true` in root-owned config and switched from the console. Manual hold is a console action. The ERP runs as a VM delivered through `box1-org/legacy-erp`;
- telemetry: `asset-service` exposes a bounded chaos control API under `/api/v1/control/*`, with stop-all, behind its `chaos-operator` role. It requires `azp=asset-service` on tokens, which blocked the console from calling it;
- Keycloak: client roles declared in `spec.roles` are not created by the operator ([#59](https://github.com/box1-org/box1-docs/issues/59));
- Kafka and release gates: which dead-letter topics and release-gate checks exist, for `poison-event` and `bad-artifact-gate`.

**Design decisions to record before implementation:**

- the mechanism for each scenario: service API, guided console step, VM-level, or not yet possible. Record the last honestly rather than faking it;
- how fixture sites and stock are seeded: the restock endpoint, or an inventory-service change that needs the user's approval;
- which tokens each called service accepts, and the Keycloak client and roles for the controller. A GitOps PR that needs approval; check the roles exist after sync;
- Kubernetes RBAC for VM-level faults (`erp-unavailable`) and `broker-outage`: the minimal verbs and resources, in a GitOps PR that needs approval;
- the demo namespace allowlist, which the user names;
- TTL, crash recovery, and how an abandoned run is detected and reset;
- audit storage and retention;
- the database credential while [#41](https://github.com/box1-org/box1-docs/issues/41) is open;
- how the stardate is computed for display;
- how the operator console (#18) adopts this fixture set and the catalog's display titles.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Every scenario's mechanism classified, with evidence |
| 3 Implementation | No arbitrary exec, shell or URL fetch; every fault has a TTL and a reset |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs; the Security pass covers authorization, the allowlist and RBAC |
| 6 Delivery | Release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | "Make it so", "The Trouble with Tribbles" and one guided ERP scenario on the cluster, with audit and end-state evidence, after approval |

**Verification scenarios:** start in a non-allowlisted namespace; unknown scenario name; TTL expiry with the controller killed mid-run; stop and reset; seeding twice; tribble contention with two simultaneous orders; a guided step not performed; anonymous request; request without the role; `red-alert` stopped through the telemetry service's stop-all; audit record complete for every run; no data outside the fixture set changed.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
