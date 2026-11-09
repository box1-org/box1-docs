# Edge sites 05 — asset-service ingests site readings and raises a stale-site alert

> **Service work in asset-service and its GitOps workload.** Readings from the two site VMs reach asset-service through Kafka, without duplicates after a replayed backlog, and a stale-site alert fires when a site goes quiet. Read `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Merging to asset-service `main` starts its build and dev promotion: approval needed.
- Detaching a site NIC and replaying a backlog on the cluster are fault injections: approval needed, site VMs only.
- The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not use Chrome.

**Issue:** [box1-docs#128](https://github.com/box1-org/box1-docs/issues/128), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- `02_site_forwarder_outbox.md`: readings on Kafka from both sites.
- `04_site_status_sites_map.md`: the heartbeat and last-seen metric the stale-site alert also uses.
- Related: [#62](https://github.com/box1-org/box1-docs/issues/62) (machine identity for HTTP ingestion), not required, because sites publish through Kafka.

## Mission

Make asset-service treat `site_ds9` and `site_spacedock` readings from the VMs like any other readings: stored once, in stable order, with the existing threshold and hysteresis alerts. Add a stale-site alert that fires when a site sends neither readings nor a heartbeat for a stated window and clears when it returns.

## Verified baseline (observed 2026-11-09; verify before relying)

asset-service main `95bf5c8`; `box1-workloads-dev` main `b95b99b`.

- **Consumer** (`application.properties` L123–139): topic `box1.telemetry.events.v1`, group `asset-service`, offset reset `earliest`, DLQ `box1.telemetry.dlq.v1`, one ordered worker. Non-reading event types are acknowledged and ignored (`EventParser.java` L47–49).
- **Deduplication is on the natural key, not `eventId`.** `reading` has primary key `(asset_id, metric_name, measured_at)` (`V1__telemetry_schema.sql` L4–15); `source_event_id` is not unique; inserts use `ON CONFLICT DO NOTHING` (`TelemetryStore.java` L30–32). Because `TELEMETRY.md` derives `eventId` from the same three fields, the two are equivalent **if** site-gateway follows that derivation (`02`).
- **Threshold and hysteresis:** `domain/ThresholdEngine.java` L1–64, called from `ReadingProjector.java` L83; limits at `application.properties` L175–204; overrides asset, then site, then metric (`MetricCatalog.java` L51–54). Whether a duplicate (conflicting) insert still reaches the threshold engine is **not verified**.
- **Staleness** is per asset only: `asset.stale-after` PT2M, gauge `asset.assets.stale`.
- **The synthetic generator** runs in-process in asset-service (`control/RunManager.java`, `RunScript.java`, `/api/v1/control/*`). Its sites are synthetic, `site_load_NN` with assets `asset_load_NN_MM` (`RunConfig.java` L14–19); it does **not** produce `site_ds9` or `site_spacedock` today. The `scenario-controller` `red-alert` scenario is `NOT_YET_POSSIBLE` (`scenarios.yaml` L137–147). No other producer for the fixture assets was found.
- **PrometheusRule:** `box1-workloads-dev/workloads/asset-service/prometheusrule.yaml` L14–22 has only `Box1ServiceDown`. Convention: label `openshift.io/prometheus-rule-evaluation-scope: leaf-prometheus`, group `box1-<svc>`, interval 30s, alerts named `Box1<Thing>`. Metrics are scraped from `/q/metrics` by a ServiceMonitor.
- Fixture assets: `asset_replicator_spacedock` (temperature) at `site_spacedock`, `asset_litterbox_transporter_ds9` (vibration) at `site_ds9`.

## Decided design

From the issue and #126's decisions.

- asset-service consumes site readings from `box1.telemetry.events.v1` (the readings topic; `02` keeps readings there). If `01` placed readings on the site topic instead, add that subscription and record it.
- Deduplication: keep the natural-key guarantee and add an explicit `eventId` check only if the natural key and `eventId` can disagree (record the reasoning). A duplicate must not re-trigger the threshold engine.
- The existing threshold and hysteresis alerts apply unchanged.
- **Stale-site alert:** a `Box1SiteStale` PrometheusRule in `box1-workloads-dev/workloads/asset-service/prometheusrule.yaml`, firing when a site's last reading and last heartbeat are both older than a stated window, and clearing when either resumes. It uses per-site metrics from asset-service (`04`'s last-seen age, plus a per-site last-reading age added here). Labels carry `siteId`.
- The synthetic generator must not produce data for `site_ds9` or `site_spacedock`. Today it does not; add a guard (reject those site IDs in a run configuration) so a future change cannot.

## Scope and guardrails

**In scope:** asset-service consumer, store and metrics changes, tests, the contracts ref bump, the PrometheusRule, and the generator guard.

**Out of scope:** site status endpoints (`04`), the site forwarder (`02`), #62.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #128 only with the evidence named.

- [ ] Readings from both VMs appear in asset-service under `site_ds9` and `site_spacedock`, and a time-window query returns them in stable order.
  - Evidence: two identical time-window API queries returning the same ordered results, and the matching Kafka records with their `causationId`.
- [ ] A threshold breach at a site raises one alert and later clears it, and the trace runs from the site to the alert.
  - Evidence: the simulator configured to breach (seeded), one `equipment.threshold-exceeded.v1` and one clear, and the trace ID in Observe → Traces (needs `07`; until then record the cluster-side spans and mark the site span `not verified`).
- [ ] Replaying a site backlog creates no duplicate readings or repeated alerts.
  - Evidence: a replay of an already-published window (for example, by resetting the site outbox rows to unpublished, approved), with reading counts and alert counts before and after.
- [ ] Detaching a site's NIC raises the stale-site alert within the stated window, and it clears after reconnection.
  - Evidence: the approved detach, the alert's firing and resolved timestamps from Alertmanager or the console, and the window.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/128-site-ingestion/`.

**Discovery must cover**
- Whether the projector and threshold engine run on a conflicting insert.
- The heartbeat metrics from `04` and the reading metrics already exposed.
- Every producer of `site_ds9` and `site_spacedock` readings, including scenario-controller and the console's load and chaos pages.
- The first-consumption offset behaviour for a site's first backlog.

**Design decisions to record**
- The stale window and its relation to the heartbeat interval and `04`'s offline threshold.
- Whether to add an `eventId` uniqueness check.
- Metric names and labels (avoid high cardinality).

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 3 Implementation | A duplicate-reading test proving no second alert |
| 6 Delivery | asset-service promoted by digest; PrometheusRule reconciled by Argo |
| 7 Live acceptance | All four criteria |

**Verification scenarios**
- Out-of-order readings after a replay; a reading older than the stale window arriving late (must not clear the alert falsely, or document that it does); a site with heartbeats but no readings; asset-service restart during a backlog drain.

**Stop conditions**
- Readings from the sites do not use the `TELEMETRY.md` `eventId` derivation and `02` cannot change.
- Sites are not yet producing on Kafka.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the alert, its window, metric names, the asset-service digest, evidence, and rollback (revert the promotion; the PrometheusRule is reverted by its GitOps PR).

Tick the completed items on #128.
