# Run #19 scenario controller: architecture review

Reviewer: architecture pass, read-only. Inputs read:

- `run19-scenario-controller` at `e061f6d` (diff vs `203968e`)
- `run19-inventory-service` at `fca04be` (diff vs `094772a`)
- `run19-workloads/workloads/scenario-controller/deployment.yaml` at `bbc6d27`
- requirements `01-services/09_scenario_controller.md` and `00-shared/06_RESOURCE_AND_SECURITY_BOUNDARIES.md`
- `box1-ops-contracts` `origin/main` and run decisions D-008, D-010, D-011

I did not run any code. Every claim below comes from reading the code. Items I could not settle by reading are marked **uncertain**.

## Findings

### ARCH-1 (medium): A rolling deploy lets two pods own one run, and the new pod resets stock under the old pod's live thread

- **Where:** `Engine.java:193-209` (`onStart` → `recover`), `run19-workloads/.../deployment.yaml:13-17` (`RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0`).
- **Problem:** D-008 assumes one replica. With `maxSurge: 1`, a rollout starts the new pod while the old pod is still serving. The new pod's `recover()` treats every open run as left over by a dead process. Its `active` is null, so the filter at `:200` matches, and it calls `halt(r, ABORTED_RESTART, …)`. That ends the run in the database and restores its fixture stock (`finish` → `restore`). Meanwhile the old pod's thread keeps running.
- **Failure scenario:** `inventory-contention` is waiting on order decisions when Argo rolls out a new image.
  1. The new pod marks the run `ABORTED_RESTART` and restocks `site_ds9/CAT-TRIBBLE-TOY`.
  2. The partial unique index now permits a new start. An operator starts a second contention run on the new pod, while the old pod's thread is still polling and has stock reads in flight.
  3. Both runs now share the same single tribble.

  This breaks the "one open run" invariant (`architecture.md:28`) and the "exactly one reservation" check. The audit records a restart that did not happen.
- **Fix:** Pick one of these:
  - Use `strategy: Recreate` for this Deployment.
  - Record an owner (pod name plus heartbeat column) on `scenario_run`, and have `recover()` abort only runs whose heartbeat is stale.
  - Hold a PostgreSQL session advisory lock as a leader lock. Only the leader starts runs or recovers them.

  Whichever you choose, also document "single replica, Recreate" in D-008 and the runbook.

### ARCH-2 (medium): `halt()` interrupts by raw thread reference and unconditionally clears `active`, so it can hit the next run

- **Where:** `Engine.java:62-66, 122-127, 258-269, 252-254`.
- **Problem:**
  - `Handle.thread()[0]` is the single shared pool thread. It is not tied to the run's task: the array is non-volatile, and the field is never cleared when the task ends.
  - `halt(A)` reads `active` once (`:259`). If A finishes on its own and B is started before `halt(A)` reaches `thread.interrupt()` (`:265`), the interrupt lands on B's task.
  - Line `:268` then sets `active = null` unconditionally, which erases B's handle.
- **Failure scenario:**
  1. A `stop` for run A races with A's natural finish, and run B is started in that window.
  2. B's `Thread.sleep` in `RunContext.await` throws `InterruptedException`. `execute` maps that to `result = null` (`:238-239`), so B's thread ends without finishing B.
  3. B stays open with no thread until the sweep expires it, up to 3600 + 30 s later. That blocks every other start in the meantime.
  4. Because `active` was cleared, a later `stop B` skips the interrupt and the wait.

  The window is narrow but real.
- **Fix:**
  - Keep the run's `Future` from `worker.submit` in `Handle`, and stop the run with `future.cancel(true)`. That interrupts only that task.
  - Make `active` an `AtomicReference<Handle>` and clear it with `compareAndSet(handle, null)` in both `halt` and `execute`.

### ARCH-3 (medium): `erp-crash-after-commit` reports VERIFIED without observing the operator step, and an unperformed step leaves the crash armed for unrelated work

- **Where:** `ErpCrashAfterCommit.java:27-47`.
- **Problem:**
  - The run displays "arm the one-shot crash" and places the order immediately ("The order follows now"). It never waits for the arming or observes it, and it returns `Result.verified(...)` whenever the order ships exactly once.
  - The requirement says: "Guided ERP scenarios … verify the result before reporting success; a step not performed times out and is reported as not verified." Here a step that was not performed gives VERIFIED.
  - D-010 records "verifies only through outcomes", but the result label still says VERIFIED.
- **Failure scenario:** The ERP is in AUTO and ships within seconds, before the operator has armed anything, so the run reports VERIFIED. If the operator then arms the crash, it stays armed. It fires on the next unrelated shipment commit, such as a console (#18) demo order, possibly long after the run ended. `RESET_GUIDED` ("if the crash is still armed, disarm it") depends on someone reading `resetDetail`.
- **Fix:**
  - Report `NOT_VERIFIED` with an explicit "crash not observable; outcome only" detail. Or add a distinct outcome (for example `VERIFIED_OUTCOME_ONLY`) so the crash is never claimed.
  - Order the steps so the order is placed only after an observable precondition. **Uncertain:** whether the adapter exposes any reconnect or redelivery signal that would show the ERP restarted.
  - At minimum, make the README and catalog `expectedObservation` say that the crash itself is not verified.

### ARCH-4 (medium): Guided ERP faults are not bounded by any TTL

- **Where:** `scenarios.yaml:53-86`, `docs/runbook.md:41-42`; ERP `docs/DESIGN.md:27`.
- **Problem:**
  - The ERP delay setting, the armed one-shot crash and a manual hold have no expiry in the ERP. The controller cannot undo or observe them; it ends with `RESET_GUIDED` and instructions.
  - The acceptance criteria require that every named fault have a bounded duration, and that an interrupted orchestration not leave a fault enabled beyond its TTL.
  - The runbook's sentence "No fault the controller enables can outlive its TTL: the controller itself enables none" is literally true, but it hides that the faults these scenarios rely on can outlive the run indefinitely. A delay of 90 s or more stays in force for every later order until someone resets it.
- **Fix:** Record this as an explicit acceptance gap in the ledger and the handoff, not as satisfied, with a backlog issue. One possible permanent fix is an ERP-side TTL on demo-mode settings in `box1-ops-erp-simulator`. That is a change to another service, so it needs the user's approval. Until then, make the run's reported outcome name the pending undo prominently. For example, the run view could carry `pendingOperatorUndo: true` until an operator acknowledges it.

### ARCH-5 (low): A stop that races a finishing thread is recorded as FAILED or VERIFIED, and can turn a good reset into RESET_FAILED

- **Where:** `Engine.java:234-251, 258-273`; `Http.java:71-73`.
- **Problem:** `halt` sets the stop flag, interrupts the thread, waits for the worker to go idle, and only then calls `finish(STOPPED)`. The first ending wins, so whatever the thread records first is kept:
  - Interrupting an in-flight HTTP call outside `await` turns into an `UpstreamException` ("…was interrupted"). It is caught as a `RuntimeException` (`:242`), so the run ends **FAILED** rather than STOPPED.
  - An executor that returns normally after the flag is set ends **VERIFIED** or **NOT_VERIFIED**.
  - If the interrupt arrives while the worker is inside `finish` → `restore` (`:292`), the restock HTTP call fails and the run is recorded `RESET_FAILED` for a reset that would have succeeded.
- **Fix:**
  - In `execute`, if `handle.stop().get()` is true after the executor returns or throws, set `result = null` and let `halt` record STOPPED.
  - Do not interrupt a thread that is already in `finish`. Use the `Future.cancel` approach from ARCH-2, cancelling only before `finish` begins. For example, set a "finishing" flag before calling `finish`.

### ARCH-6 (low): Partial failures leave a run without its reset, or a run open with no thread, and nothing retries

- **Where:** `Engine.java:111-127, 284-298, 197-209`.
- **Problem:**
  - (a) `finish` commits `store.end(...)` (`:286`) before the HTTP restore and `resetResult`. If the process dies or the store fails in between, the run is ended with `reset_result IS NULL`. `recover()` looks only at open runs, so the reset is never retried.
  - (b) The same applies when recovery at startup gets `RESET_FAILED` because inventory is not up yet. Nothing retries it.
  - (c) In `start`, a `StoreException` from `store.impact`/`store.find` (`:118`, `:123`) after a successful insert leaves an open run that has no thread and no `active` handle. Every start is then blocked until the sweep runs at TTL + 30 s, which can be about an hour.
- **Fix:** Have the sweep also retry reset for ended runs whose `reset_result` is NULL or `RESET_FAILED`, with a bounded number of attempts. Those runs are identifiable. In `start`, wrap the steps after the insert so that a failure ends the run immediately as FAILED.

### ARCH-7 (low): A catalog entry removed while a run is open stops the controller from starting

- **Where:** `Engine.java:260` (`catalog.find(run.scenario()).orElseThrow()`), called from `recover()` at startup (`:193-195`) and from the sweep.
- **Problem:** `recover()` catches only `StoreException`. Suppose a deploy renames or removes a scenario while one of its runs is open. The `NoSuchElementException` escapes the `StartupEvent` observer, which (**uncertain**, but this is normal Quarkus behavior) fails startup, so the pod crash-loops. In the sweep, the same exception would repeat every 5 s.
- **Fix:** If the scenario is no longer in the catalog, end the run as ABORTED with the reset recorded as `RESET_FAILED: scenario no longer in catalog`. Alternatively, keep the needed reset data (fixture records) on the run row at start, so the reset does not depend on the current catalog.

### ARCH-8 (low): The allowlist gates where the controller runs, not what it touches

- **Where:** `Gate.java:29-39`, `application.properties:39-42`, `ScenarioSettings.java:21-25`.
- **Problem:** Gate 2 compares only the controller's own namespace (`POD_NAMESPACE`) with the allowlist. The upstream base URLs are separate configuration that nothing checks. A deployment in an allowlisted namespace with `ORDER_SERVICE_URL` or `INVENTORY_SERVICE_URL` pointed at a non-demo environment would pass every gate and place orders or restock there. Today all targets are `*-dev`, so this is defense in depth.
- **Fix:** At startup, parse `<svc>.<namespace>.svc` from each upstream URL. Fail closed, by refusing every scenario with a plain message, unless each target namespace is on a target allowlist.

### ARCH-9 (low): The controller's inventory identity is broader than the fixture work needs

- **Where:** `run19-workloads/.../deployment.yaml` (`INVENTORY_TOKEN_CLIENT_ID=scenario-controller`), `architecture.md:13`, inventory `AdminResource.java:36` (class-level `@RolesAllowed(inventory-admin)`).
- **Problem:** The controller limits itself in code (`FixtureService.restore` checks `Fixtures.isFixtureStock`). The credential it holds, `inventory-admin`, can also release any reservation, restock `site_nyc`/`site_bos` and create arbitrary sites. If the client secret leaks, or a controller bug slips through, the blast radius is all of inventory admin, not the fixture set.
- **Fix:** Follow-up in inventory-service, which needs approval: a narrower role (for example `inventory-fixture-admin`) limited to create-once and restock, and possibly to a fixture site prefix list. Release would stay with `inventory-admin`. Record this as a backlog item.

### ARCH-10 (low): Catalog, executors and reset can drift apart, and reset is not refused while another scenario is running

- **Where:** `Catalog.java:51-65`, executors' hard-coded `SITE`/`SKU` (for example `BaselineOrder.java:12-13`), `FixtureService.recordsFor` (`:76-78`), `Engine.reset` (`:149-166`).
- **Problem:**
  - The reset scope comes from the catalog's `fixtures`, but the stock a run actually consumes comes from Java constants. Startup validation does not check that each executor's site/SKU is in its catalog `fixtures`, or that catalog fixture IDs exist in `Fixtures`.
  - `reset X` while a run of Y is open restocks X's records immediately. That is safe today only because the stock records of the five available scenarios do not overlap (I checked them: spacedock/SPOT-BOWL, ds9/TRIBBLE, utopia/COMBADGE, spacedock/PHASER, ds9/DILITHIUM).
  - Operator-step text exists twice, in the YAML `operatorSteps` and as Java strings, so it can drift.
- **Fix:**
  - Add a startup check that each executor declares its records and that they are a subset of `recordsFor(catalog.fixtures)`.
  - Validate catalog fixture IDs against `Fixtures`, and check that stock records do not overlap across available scenarios.
  - Refuse `reset` while any run is open (409), or else document that records must stay disjoint.

### ARCH-11 (low): A retention setting under 90 days makes the daily purge fail every day

- **Where:** `V1__scenario_schema.sql:43-49` (the trigger permits deletes only below `now() - 90 days`), `Engine.java:212-216`, `application.properties:46` (`SCENARIO_AUDIT_RETENTION`, configurable).
- **Problem:** If `SCENARIO_AUDIT_RETENTION` is set below `P90D`, the `DELETE` matches rows the trigger refuses. The whole statement then raises, and the scheduled job throws `StoreException` every day without deleting anything. The setting looks tunable but effectively is not.
- **Fix:** Validate `retention >= P90D` at startup, or drop the configuration and hard-code 90 days to match the trigger.

### ARCH-12 (low): The two inventory create-once routes treat migration-seeded resources differently

- **Where:** inventory `ReservationService.java:+240-269`, `docs/runbook.md` table.
- **Problem:**
  - `PUT /internal/v1/sites/site_nyc {"status":"ACTIVE"}` returns **200 "exists with this status; nothing changed"** for a V2 migration-seeded site. `PUT /internal/v1/stock/site_nyc/SKU-42` returns **409** for a seeded record, because there is no `OPENING` movement. Callers cannot tell from a site-create 200 whether the site was registered through the API, since `site_registration` has no row for it.
  - `createStock` also accepts new SKU rows on the V2 lab sites (`site_nyc`, `site_bos`, `site_closed`). That is additive, but it widens the lab fixture that existing tests count on. The runbook's claim that the V2 fixture "is safe from them" holds for existing rows only.
- **Fix:** Pick one rule. Either return 409 for a site with no `site_registration` row, matching the stock route, or return 200 for both. Document the choice in the contract. Optionally refuse `createStock` on sites that were not registered through the API.
- **Concurrency of these routes:** no finding. A concurrent duplicate `INSERT … ON CONFLICT DO NOTHING` waits for the first transaction to commit, then the follow-up read (`siteStatus` / `openingQuantity`) sees the committed row under READ COMMITTED. The unique `OPENING` index backs this up.

### ARCH-13 (info): Contract coverage gaps

- **Where:** `ContractTest.java:68-77`, D-011, `OrderApi.java:70-73`, `AdapterApi.java:14, 42-46`.
- **Detail:**
  - The two new inventory routes are not in `box1-ops-contracts` `origin/main` `openapi/inventory-service.yaml`. I confirmed that only `/restock` and `/release` appear under `/internal`. D-011 tracks this, with a patch in `evidence/02-inventory-contract.patch`. The controller's `ContractTest` asserts `restock` but not the two `PUT` routes the seeding depends on, so once the contract lands, nothing would catch a change to them.
  - The controller also depends on two things that are in no contract: order-service's internal `ful_<suffix>` naming (fails closed on a mismatch, documented as #18 G-1) and the adapter's `fulfillment_held` Prometheus metric name. No fulfillment-adapter OpenAPI exists in contracts.
- **Fix:** When the D-011 patch lands, add assertions for `PUT /internal/v1/sites/{siteId}` and `PUT /internal/v1/stock/{siteId}/{sku}`. Track an adapter contract (status view and held metric) as a follow-up.

## No findings (checked explicitly)

- **Owns its state; no cross-service table reads:** the controller uses only its own PostgreSQL (`scenario-controller-postgres`, `scenario_run`/`scenario_audit`). All other data comes over HTTP through public or admin APIs (`OrderApi`, `InventoryApi`, `AdapterApi`). It has no other datasource.
- **Not a command runner:** there is no `ProcessBuilder`, `Runtime.exec`, Kubernetes client or shell. `automountServiceAccountToken: false`. Base URLs are fixed in configuration. Every path segment goes through `Http.segment` (`^[A-Za-z0-9_-]{1,128}$`), redirects are disabled, and every call has a timeout. Scenario names are pattern-checked and catalog-checked before use; unknown names are refused (404) and audited. NOT_YET_POSSIBLE scenarios have no code and are refused (409) and audited.
- **Explicit state transitions:** the states are an enum with a DB CHECK. Endings use a conditional `UPDATE … WHERE ended_at IS NULL`, so the first ending wins. `progress` cannot reopen an ended run. The partial unique index enforces one open run at the database level. The race problems above are about *which* ending wins, not about illegal states.
- **No accidental distributed transaction:** seeding is a sequence of idempotent create-once calls; a re-run completes a partial seed. Reset uses reset-scoped idempotency keys. Order creation uses run-scoped `stardock-<runId>-<n>` keys. Nothing spans the local DB and a remote call atomically. The only gap is the end-then-reset ordering in ARCH-6.
- **Declarative catalog:** YAML loaded at startup with unknown-property failure, name, duration (≤3600 s) and reason validation, and a fail-fast check that every AVAILABLE scenario has an executor. Caveats are in ARCH-10.
- **Fixtures only additive, through service APIs:** seeding uses inventory's create-once routes; reset only restocks, only for records `Fixtures.isFixtureStock` approves, and only up to the opening quantity of *available* stock. Nothing is released, cancelled or reduced. Customers need no seeding. Assets are not touched, since `red-alert` is NOT_YET_POSSIBLE. **Nothing outside the fixture set is touched**, with the ARCH-9 credential caveat.
- **TTL bounds on controller activity:** every wait is capped by `expiresAt`, a TTL may only be lowered, the sweep runs every 5 s with a 30 s grace, and a restart aborts and resets. Caveats are in ARCH-1, ARCH-4 and ARCH-6.
- **Audit trail:** append-only by trigger (update, delete and truncate are refused except retention deletes); refusals are audited as DENIED. The stardate is display-only.
- **Inventory create-once semantics:** routes are authenticated (`inventory-admin`) and validated (site ID, SKU, status enum, quantity 0..1e6, reason). The design is insert-only (`ON CONFLICT DO NOTHING`). A repeat returns 200, and a conflicting repeat returns 409. Site registrations and `OPENING` movements are immutable, at most one `OPENING` per record. Concurrency is safe. Consistency notes are in ARCH-12.
