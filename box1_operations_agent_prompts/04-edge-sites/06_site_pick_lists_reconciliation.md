# Edge sites 06 — Site pick lists, and pick/count events into inventory-service with reconciliation

> **Site app and service work.** Each site receives its pick list; site picks, cycle counts and holds flow back to inventory-service, which applies them exactly once and resolves conflicts with central stock by a documented rule. **Inventory only:** the order → ERP → ship flow does not change. Read `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Merging to a service `main` starts its build and dev promotion: approval needed.
- Inventory data is shared persistent state. Destructive migrations or data resets need approval.
- Detaching a site NIC is a fault injection: approval needed, site VMs only.
- The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not use Chrome.

**Issue:** [box1-docs#129](https://github.com/box1-org/box1-docs/issues/129), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126). Gating orders on a site pick is the future enhancement [#134](https://github.com/box1-org/box1-docs/issues/134) and is out of scope.

**Dependencies**
- `01_site_foundation.md`: the `site.*.v1` contracts and the site topic. Field semantics in those contracts must match this prompt's design; agree them before `01` merges, or extend them here with a reviewed contracts PR.
- `02_site_forwarder_outbox.md`: the site outbox and its delivery to Kafka.
- [#138](https://github.com/box1-org/box1-docs/issues/138): the site instances.
- Per-site Kafka read restrictions wait on [#71](https://github.com/box1-org/box1-docs/issues/71) (see `03`).

## Mission

1. **Down:** site-gateway consumes reservation events for its own `siteId` and keeps a local pick list that stays usable while the site is offline.
2. **Up:** `site-ops` (Qute + htmx, handheld style) records pick confirmations, cycle counts and stock holds into the site outbox.
3. **Central:** a new inventory-service consumer applies site events idempotently by `eventId`, resolves conflicts with a documented rule, and audits every decision.

## Verified baseline (observed 2026-11-09; verify before relying)

inventory-service main `2f37881e`; `box1-ops-contracts` main `7b7fbac5`.

- **Reservation events:** `inventory.reserved.v1` (`orderId`, `reservationId`, `sku`, `quantity`, `siteId`, `expiresAt`; one SKU per reservation) is built in `EventFactory.java` L30–41 from `ReservationService.java` L85. `box1.inventory.events.v1` is keyed by `orderId`, 3 partitions, 7 days, and also carries `inventory.rejected.v1` and `inventory.reservation-expired.v1`. Shipment results are on `box1.fulfillment.events.v1`.
- **Consumers:** `box1.order.events.v1` and `box1.fulfillment.events.v1`, group `inventory`, DLQ `box1.inventory.dlq.v1` (`application.properties` L37–64, L75). Deduplication table `processed_event` (`V1` L135–139).
- **Stock model:** `inventory_site(site_id, status)`, `inventory_stock(site_id, sku, on_hand, reserved, CHECK on_hand >= reserved)` (`V1` L2–15). `reservations.order_id` is unique.
- **Audit:** immutable `stock_movement` with kinds `SEED`, `RESTOCK`, `SHIPMENT`, `LATE_SHIPMENT` and `OPENING` (V3 L16–18) and a unique `idempotency_key`; `reconciliation_item` (OPEN/RESOLVED, unique `(event_id, kind)`, `V1` L97–112) with kinds in `ReservationService.java` L109–187. **The `stock_movement` kind CHECK must be extended** for pick or count kinds.
- **Shipment already moves stock.** A confirmed shipment records a `SHIPMENT` movement. If a site pick also decremented `on_hand`, the same unit would leave stock twice. Confirm the exact effect of `shipment.confirmed.v1` on `on_hand` and `reserved` in discovery.
- **Outbox caveat:** `ux_outbox_once_per_order(aggregate_id, event_type)` (`V1` L131) allows one event of each type per aggregate. Any new inventory event keyed by site or SKU must not collide with it.
- **Seed sites differ:** Flyway `V2` seeds `site_nyc`, `site_bos`, `site_closed`; the fixture sites (`site_ds9`, `site_spacedock`, …) are seeded through the admin API by `scenario-controller` (`Fixtures.java` L21–25, stock L51–64).
- Flyway's last migration is `V3`.

## Decided design

From the issue and #126's decisions. The rows marked **decide** must be recorded before code depends on them.

**Down to the site**
- site-gateway consumes `box1.inventory.events.v1` (and the cancellation and shipment signals it needs from `box1.order.events.v1` / `box1.fulfillment.events.v1`) with a per-site consumer group, keeps events whose `siteId` matches, and stores the pick list in the site PostgreSQL.
- An item leaves the pick list when it is picked, when its reservation expires or is released, or when it ships. **Decide** which events drive removal.
- A reservation at `site_ds9` reaches only `site-west`; one at `site_spacedock` reaches only `site-east`.

**Up from the site (`site-ops`)**
- Pick confirmation → `site.pick-confirmed.v1`; cycle count → `site.stock-adjusted.v1`; hold placed or released → `site.stock-held.v1` (names from `01`).
- Written to the site outbox in the same transaction as the local change; usable offline.

**In inventory-service**
- A new consumer on the site topic, group declared in `TOPICS.md`, deduplicating through `processed_event`.
- **Decide pick semantics.** Recommended: a pick confirmation records that the reserved units were physically picked (a `PICK` audit entry and a reservation state), and does **not** change `on_hand`, because the shipment already does. Record the alternative considered.
- **Cycle count:** sets the site's counted quantity for a SKU, recorded as a `COUNT` movement with the delta.
- **Reconciliation rule (decide and document):** for example, a count taken at time T while offline is applied relative to reservations and shipments after T, and never drives `on_hand` below `reserved`; when it would, the count is applied up to the limit and a `reconciliation_item` (`COUNT_CONFLICT`) is opened for an operator. The rule must be deterministic for any arrival order.
- Every decision writes an audit record an operator can see (existing reconciliation view or the console).
- Holds: **decide** whether a hold reduces available stock centrally or is site-local only.

## Scope and guardrails

**In scope:** `site-gateway` `gateway` (pick-list consumer) and `ops` (Qute + htmx UI) modules; inventory-service consumer, migrations (additive), audit and tests; contracts changes if `01` did not cover them; the operator view of reconciliation items.

**Out of scope:** order gating (#134); changing order, fulfillment adapter or ERP behaviour; Kafka ACLs (#71, `03`).

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #129 only with the evidence named.

- [ ] A reservation at `site_ds9` appears on site-west's pick list, and a reservation at `site_spacedock` appears only on site-east's.
  - Evidence: two orders placed through the order API, the `inventory.reserved.v1` records, and both sites' pick lists (UI screenshot or local query).
- [ ] A pick confirmation and a cycle count from a site change inventory-service as the contract states, exactly once, including after a replayed backlog.
  - Evidence: stock and movement rows before and after, the same events replayed, and unchanged rows after the replay.
- [ ] A count that conflicts with central stock is resolved by the documented rule, with an audit record visible to an operator.
  - Evidence: a count taken with the site's NIC detached (approved) while a new reservation is made centrally, the outcome after reconnection, the rule text, and the audit record in the operator view.
- [ ] Order processing and ERP shipping are unaffected.
  - Evidence: an order placed, reserved, fulfilled and shipped through ERP during the run, with its timeline, and no new reconciliation kinds on that order.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/129-site-picks/`.

**Discovery must cover**
- The effect of `shipment.confirmed.v1`, release and expiry on `on_hand` and `reserved`.
- The fixture stock for `site_ds9` and `site_spacedock` on the cluster.
- The merged site contracts and topic.
- The existing operator view for reconciliation items.

**Design decisions to record**
- Pick semantics; count reconciliation rule; hold semantics; pick-list removal triggers.
- The site's consumer group and first-start offset.
- Migration numbers and new movement and reconciliation kinds.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 1 Design | The reconciliation rule written with worked examples before code |
| 3 Implementation | Property or table tests of the rule over arrival orders |
| 4 Verification | Replay and offline-count scenarios pass locally |
| 6 Delivery | inventory-service promoted; site OS digest carrying the new modules on both sites |
| 7 Live acceptance | All four criteria |

**Verification scenarios**
- Pick confirmed for a reservation that expired meanwhile; count arriving before an earlier pick from the same site; duplicate count events; a count for a SKU the site does not stock; a reservation for an UNAVAILABLE site; site offline for longer than the reservation TTL.

**Stop conditions**
- The pick semantics would change order or shipment behaviour.
- A breaking contract change is needed after consumers pinned `01`'s contracts.
- A destructive migration would be needed.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the rule, contracts commit, service and site digests, evidence, and rollback (revert the inventory promotion; migrations are additive; site events stay in the site topic for replay).

Tick the completed items on #129.
