# Run #19 messaging / integration review — scenario controller + inventory fixture admin

Scope: `run19-scenario-controller` `203968e..e061f6d`, `run19-inventory-service` `094772a..fca04be`, read against upstream
order-service / inventory-service / fulfillment-adapter sources (disc-a), `box1-ops-erp-simulator/docs/DESIGN.md`, contracts
`origin/main` (ORDER-STATE.md, openapi/order-service.yaml). Read-only; nothing was built or run.

## Findings

### MSG-1 — Medium — duplicate-shipment check in `erp-crash-after-commit` cannot fail
`scenarios/ErpCrashAfterCommit.java:39-42` (same pattern `BaselineOrder.java:52`, `ErpDelayedProcessing.java:60`).
The check counts `TRANSITION` entries with `toState=SHIPPED`. Order-service only allows `SHIPPED` from
`FULFILLMENT_REQUESTED` (`order-service Transitions.java:40-50`; ORDER-STATE.md "Any other pair → timeline note"), so a
second `shipment.confirmed.v1` after a crash/recovery becomes a `NOTE` (`IGNORED_SHIPPED` / `IGNORED_COMPLETED`), never a
second transition. `shipments != 1` is therefore always false once SHIPPED is observed, and the check runs immediately
after the first SHIPPED is seen, before a post-restart re-publication could even arrive.
Failure scenario: ERP crashes after commit, restart re-publishes with a new eventId/shipmentId; inventory records
`SHIPMENT_DUPLICATE`, order notes it; controller reports VERIFIED "shipped exactly once".
Fix: after SHIPPED, wait a settle window (e.g. 30-60 s, bounded by TTL), then fail if the timeline has any NOTE with
`eventType=shipment.confirmed.v1` (or reasonCode `IGNORED_SHIPPED`/`IGNORED_COMPLETED`/`FULFILLMENT_REQUEST_MISMATCH`)
for the order, and/or cross-check the adapter's `shipmentId` is unchanged at the end. Keep the transition count only as
a sanity check.

### MSG-2 — Medium — `erp-crash-after-commit` can be VERIFIED without the fault having fired
`ErpCrashAfterCommit.java:27-29, 46-47`. `awaitOperator` only records the step; the order is placed immediately with no
observable confirmation that the crash was armed. The ERP crash is one-shot on "the next shipment commit" (DESIGN.md
§faults), so any other shipment in between consumes it. Either way the order ships normally and the run ends VERIFIED.
Failure scenario: operator arms late (or another order ships first); run reports VERIFIED for a crash that never
happened on this order.
Fix: report VERIFIED only with evidence (e.g. adapter `revision`/receipt/resend data or an operator confirmation step
after the ship), otherwise a distinct outcome such as NOT_VERIFIED "crash not observed"; at minimum wait for the
operator to confirm arming before placing the order and say in the detail that the crash itself is unverified.

### MSG-3 — Medium — available-based reset over-restores when a held unit later returns; tribble scenario then fails permanently
`fixtures/FixtureService.java:64-69`, `Engine.java:292`, `InventoryContention.java:31-38`.
Reset restocks `opening - available` at the moment the run ends, while the run's own reservation is still held
(`available = on_hand - reserved`, inventory `tryHold`/`consumeHold`). If that hold is consumed by shipment the books
balance (consumeHold keeps available constant). If it is instead returned — ACTIVE hold expires (15 min TTL, e.g. order
went EXCEPTION/RESERVATION_EXPIRED), operator `release` after an ERP reject/`SHIPMENT_FAILED` (inventory runbook's
reconciliation path) — available ends above opening. Reset never reduces stock (D-007, no reduce route).
Failure scenario: tribble winner reserved (on_hand 1/reserved 1) → reset +1 (2/1) → winner's request rejected in ERP and
the hold released by an operator → available 2. Every later `inventory-contention` run fails "Expected exactly 1 …
found 2" with no automated recovery. On other fixtures this is only on-hand drift.
Fix (pick one): make contention robust to any available N≥1 by ordering `quantity = available` for both customers
(exactly one can win); or restore against holds the controller knows are terminal (skip records whose run orders are
not SHIPPED/REJECTED, and restore on the next run's setup instead); and document the manual recovery (forward migration
or release path) in the runbook.

### MSG-4 — Medium — manual-hold "released, nothing lost" accepts any non-HELD outcome and reads order state too early
`ErpManualHold.java:50-62`. Release is observed as `outcome != HELD`, which includes `REJECTED` (ERP: `HELD → reject`
is legal, DESIGN.md table). `after` is read once, immediately; an ERP reject only becomes order `EXCEPTION` after the
adapter publishes `shipment.failed.v1` and order-service consumes it, so `after` is still `FULFILLMENT_REQUESTED` and
the dead-end check passes. Nothing confirms the request progresses (release → `PENDING`, ships only in AUTO or by a
later console ship).
Failure scenario: operator presses reject instead of release; run VERIFIED "Held and released … adapter outcome
REJECTED".
Fix: require `outcome` in {`PENDING`, `SHIPPED`} for release; fail on `REJECTED`. Optionally wait (bounded) for SHIPPED
or document that only "back to PENDING, order still FULFILLMENT_REQUESTED" is verified.

### MSG-5 — Medium/Low — held signal is global, may be stale, and never gates the result
`ErpManualHold.java:45-48, 61-62`; `upstream/AdapterApi.java:43-46`. `fulfillment_held` counts all held requests and
refreshes every 15 s. `>= 1` can be satisfied by another held request (or a stale value), and when the signal is not
observed the run is still VERIFIED, with the miss only in the detail text. Requirement 09 §acceptance: a manual hold
"reproduces alert".
Fix: read the gauge before the hold step as a baseline and require an increase (`> baseline`); either make the signal
part of verification or mark the result clearly (e.g. VERIFIED only when signal observed, else NOT_VERIFIED "signal
missing"). Optionally check `fulfillment_metrics_refresh_age_seconds` is small.

### MSG-6 — Low — delay is measured to order SHIPPED, so broker/outbox lag counts as ERP delay
`ErpDelayedProcessing.java:44-59`. Start = controller's observation of adapter `ACKNOWLEDGED` (correct: ERP import writes
PENDING before the AUTO delay); end = observation of order `SHIPPED`, which includes adapter outbox backoff (max 300 s),
Kafka and order consumer lag, and the ERP's separate "pause publication" fault. Any of those ≥60 s yields VERIFIED with
no AUTO delay. Poll granularity (2 s) is otherwise fine against a 60 s threshold.
Fix: measure ERP-side: wait for adapter `outcome=SHIPPED` and use adapter `acknowledgedAt`/`statusAt` (both in the
adapter view) for the interval; then separately require order SHIPPED once.

### MSG-7 — Low — single-shot writes and reads: a timeout fails the run and can orphan an unrecorded order
`upstream/Http.java:47-75` (no retry), `OrderApi.java:32-44`, `BaselineOrder.java:23`, `InventoryContention.java:65-84`,
and non-probe reads `ErpCrashAfterCommit.java:39-40`, `BaselineOrder.java:52`, `RunContext.requireStock`.
Order creates use run-scoped keys, so a retry is safe, but none is attempted: a 5 s timeout after order-service committed
ends the run FAILED and the order ID never reaches `impact`/audit. In contention, one create can succeed while the other
throws; the successful order is also unrecorded. A transient read failure after a successful ship also turns the run
FAILED.
Fix: retry order create a bounded number of times with the same key (200 replay is the contract), record any returned ID
before failing, and route post-condition reads through a short bounded retry (or `c.await` with a small limit).

### MSG-8 — Low — stop/TTL mid-contention can let both tribble orders reserve
`Engine.java:156/189 → finish → restore`; `InventoryContention.java:40-50`. If the run is stopped after one order reserved
(available 0) but before inventory consumed the other's `order.placed`, reset restocks +1 and the second order then
reserves too. The run is STOPPED (no false verify), but persisted data shows two reservations for "the last tribble" and
on_hand 2.
Fix: on stop, wait (bounded) until all run orders are decided before restoring, or skip restore for records with
undecided run orders and leave it to the next run's setup.

### MSG-9 — Low — misconfigured adapter read policy degrades to a silent TTL wait
`AdapterApi.java:28-36`, `RunContext.java:127-132`. The controller sends no token to `GET /api/fulfillments/{id}`; the
adapter's default read policy is `authenticated` (`fulfillment-adapter application.properties:122-124`), so the run
relies on `FULFILLMENT_READ_POLICY=permit` in the deployment (as `docs/architecture.md` states). If it is not set, every
probe gets 401, `await` tolerates it as transient, and the run ends NOT_VERIFIED at TTL (up to 15-30 min) with only a log
warning.
Fix: treat 401/403 from any upstream in a probe as a run Failure with a plain message.

## No-finding areas (verified)

- **Order idempotency keys:** `stardock-<runId>-<n>` (`RunContext.key`), scoped by `X-Consumer-Id: scenario-controller`;
  contention uses distinct keys 1/2; baseline replay check expects the contract's 200 replay with the same orderId. Keys
  are ≤255 chars.
- **Restock keys:** `stardock-reset-<resetId|runId[-setup]>-<site>-<sku>` are unique per reset and record; inventory hashes
  site/sku/quantity/reason, so a reused key with a changed quantity is a 409, not a double restock. In practice a reset is
  never replayed with the same ID; a re-run reset uses a fresh `rst_` ID and recomputes from current available, so a lost
  response after a committed restock is harmless (next reset sees available = opening). A restock-response timeout shows
  as RESET_FAILED though it succeeded; manual reset recovers.
- **Create-once PUTs:** site/stock `ON CONFLICT DO NOTHING` + status/opening-quantity comparison makes repeats 200 and
  conflicting repeats 409; concurrent creates are safe under READ COMMITTED (the loser sees the committed OPENING row).
  Fixture IDs do not overlap the V2 lab fixture (`site_nyc`/`site_bos`/`site_closed`).
- **Order → fulfillment ID:** `ful_` + suffix matches order-service `OrderService.java:88-89`; cross-checked against the
  adapter's `orderId` in `Steps.acknowledged` (throws Failure, not swallowed by `await`) and in the crash scenario.
  Baseline uses the derived ID only in operator text (not cross-checked; a wrong ID would only yield NOT_VERIFIED).
- **Skipped states under polling:** `PAST_RESERVATION` and `SHIPPED` sets include all later states; `ON_SHIPMENT` policy
  (SHIPPED+COMPLETED in one transaction) is handled; default policy `none` stops at SHIPPED, which the scenarios accept.
  Dead ends (`REJECTED`/`EXCEPTION`/`CANCELLED`) end waits. Timeline is paged (20 default) but transitions are the first
  entries, so the first page suffices.
- **Contention invariant:** both orders must be decided, exactly one past reservation, exactly one REJECTED
  `INSUFFICIENT_STOCK` (inventory `classifyDenial`), and available 0; `tryHold` is a single conditional UPDATE, so the race
  is decided atomically in inventory.
- **Bounded waits:** every probe is capped at TTL (or `SIGNAL_WAIT`), each HTTP call has connect+request timeouts (5 s),
  stop/interrupt is checked each loop; sweep ends runs past TTL+30 s; restart aborts and resets open runs.
- **COMMITTED holds and later shipments:** inventory never expires COMMITTED holds, and consumeHold leaves available
  unchanged, so reset-then-ship is consistent; a late shipment after release reduces on_hand only if available allows
  (self-correcting for the tribble: next run restores from 0).
- **Inventory change and event behaviour:** the diff adds only admin PUT routes, store methods, views/validation and V3
  migration (`site_registration`, `OPENING` movement kind + unique index). No change to messaging, `ReservationService.apply`,
  outbox/event factories or topics. New sites/records only make previously unknown site/SKU pairs reservable; already
  recorded decisions are untouched (`store.outcome` short-circuits redelivery). No Java code switches on movement kind.
