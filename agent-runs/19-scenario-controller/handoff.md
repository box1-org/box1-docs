# Handoff, run 19 (box1-docs#19, scenario controller), stop 2

## Work completed
- **Workstream:** Service 09, scenario control and the Starfleet Feline Supply fixture set, `frontier` profile.
- **Repositories, branches and changed paths:**
  - box1-org/scenario-controller `run19-controller`: `src/main/**` (catalog, gates, engine, scenarios, clients, API), Flyway `V1`/`V2`, tests, `scripts/scenario.sh`, `README.md`, `docs/architecture.md`, `docs/runbook.md`, `.tekton/release.yaml` (gate), `pom.xml`.
  - box1-org/inventory-service `run19-fixture-admin`: create-once site and stock routes, `V3`, tests, runbook.
  - box1-org/box1-gitops `run19-scenario-controller-keycloak`: three `KeycloakClient`s.
  - box1-org/box1-workloads-dev `run19-scenario-controller-runtime`: controller Deployment env and `Recreate`.
- **PRs (none merged):** scenario-controller#1, inventory-service#3, box1-gitops#78, box1-workloads-dev#103.
- **Issue filed:** box1-docs#71 (Kafka authentication).

## Tests and deployment proof
- **Controller:**
  - `./mvnw -B verify` (CI set): passes in the cluster PR pipeline on `7f0f9ea`.
  - `./mvnw -B -Pcontainers verify -DskipITs=false`: 48 tests and 5 IT pass; Checkstyle 0, SpotBugs 0 (`evidence/03`).
- **Inventory:** 74 tests and 10 IT pass locally; CI green.
- **Local end to end** against real order, inventory and adapter services, the ERP harness and Keycloak 26.4: 37/37 checks after the review repairs (`evidence/07`).
- **Deployment:** none. No image digest and no GitOps commit observed. Release gates are not yet exercised.

## Contract state
- No event schema. The controller's API is its served OpenAPI.
- Inventory's two new operations need `box1-ops-contracts/openapi/inventory-service.yaml` (patch: `evidence/02-inventory-contract.patch`, not pushed).
- Migrations are additive (controller `V1`, `V2`; inventory `V3`).

## Operations and safety
- **Controller safeguards:**
  - three gates: enabled flag, `POD_NAMESPACE` allowlist and upstream host allowlist;
  - roles only from client `scenario-controller`, with an `azp` allowlist;
  - no Kubernetes RBAC, and no exec, shell or caller-supplied URL;
  - one run at a time, a TTL on every run, abort and reset on restart;
  - additive reset;
  - an append-only audit trail kept 90 days.
- **Secrets:** the inventory admin client secret comes through Secret `scenario-controller-inventory-token` (user-provisioned, approval pending). The database Secret follows the template (#41; reported directly).
- **Resources:** template defaults (100m/256Mi requests, 512Mi limit).
- **Known risks:**
  - ERP faults and holds have no ERP-side expiry;
  - `inventory-admin` is broader than fixtures need;
  - the #18 console's tokenless catalog read will get 401.
- **Rollback:** revert the workloads PR (digest-pinned), or the Keycloak PR. The inventory V3 rollback is untested, but older images ignore the new rows.

## Next agent session
- **Next slice:** Phase 6 delivery and Phase 7 live acceptance, after approvals A-1 to A-11.
- **Read first:** `checkpoint.md`, `open-decisions.md`, `requirements.yaml`, `review-findings/outcomes.md`, `evidence/07`.
- **Blockers:** approvals and decisions in `open-decisions.md`.

## Run state

```yaml
profile: frontier
issue: box1-org/box1-docs#19
current_phase: 6 Delivery (stopped at entry for approvals)
repositories:
  - name: box1-org/scenario-controller
    branch: run19-controller
    commit: 7f0f9ea
  - name: box1-org/inventory-service
    branch: run19-fixture-admin
    commit: fca04be
  - name: box1-org/box1-gitops
    branch: run19-scenario-controller-keycloak
    commit: 63c0624
  - name: box1-org/box1-workloads-dev
    branch: run19-scenario-controller-runtime
    commit: 4c039d3
run_state_path: box1-docs agent-run/19-scenario-controller:agent-runs/19-scenario-controller/
requirements:
  proposed: 3
  implemented: 2
  locally_tested: 21
  ci_verified: 5
  deployed: 0
  live_verified: 0
  blocked: 1
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [architecture, persistence, messaging, security, operations]
open_decisions: [A-1..A-11 approvals, O-11, O-13, O-14]
rollback_state: nothing deployed; nothing to roll back
next_action: on approval, merge inventory-service#3 then scenario-controller#1 and record the releases
```
