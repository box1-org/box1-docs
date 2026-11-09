# Edge sites 02 — Site forwarder: readings and site events to Kafka through a bounded disk buffer

> **Site app work in `site-gateway`.** The equipment simulator publishes readings over MQTT; the `gateway` module writes them and site events into a local PostgreSQL outbox, and a publisher drains the outbox to Kafka, buffering while the site is disconnected. Read `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Detaching a site NIC, rebooting a site VM or killing a site service on the cluster is a fault injection: it needs approval, and only on the named site VMs.
- Shared infrastructure (KafkaTopics, listeners, NetworkPolicies) changes only through an approved GitOps PR.
- The user merges. Wait about 10 seconds between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- No credential goes in Git, the bundle, the image, logs or evidence.
- Do not use Chrome.

**Issue:** [box1-docs#127](https://github.com/box1-org/box1-docs/issues/127), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- `01_site_foundation.md`: the merged contracts, the site topic, and a `site-gateway-os` image with the broker and database.
- [#137](https://github.com/box1-org/box1-docs/issues/137): the `site-gateway` repository and its bundle pipeline, which carry this code into `site-gateway-os`.
- [#138](https://github.com/box1-org/box1-docs/issues/138): `site-west` and `site-east`, for live acceptance.
- [#71](https://github.com/box1-org/box1-docs/issues/71) is open: Kafka has no client authentication until it lands. Per-site Kafka identity is `03_site_machine_identity.md`.

## Mission

Move equipment readings and site events from each site VM to Kafka, keep them on disk while the site is disconnected, and drain them on reconnection with no loss and no duplicates. The sites are `site-west` (`site_ds9`) and `site-east` (`site_spacedock`).

## Verified baseline (observed 2026-11-09; verify before relying)

- `site-gateway` does not exist yet; #137's template will generate the `gateway`, `ops` and `simulator` modules.
- **Kafka** (`box1-gitops` main `4bcc907`, `platform/kafka/kafka.yaml` L1–28): cluster `box1-kafka` in `box1-kafka`, Strimzi, KRaft, Kafka 4.2.0, one broker, replication factor 1. One listener, `plain` on 9092, internal, no TLS, no authentication, no authorization. Bootstrap `box1-kafka-kafka-bootstrap.box1-kafka.svc:9092`. There is no NetworkPolicy in `box1-kafka`.
  - The site VMs use the pod network with masquerade, so the internal bootstrap Service is the expected path. **Reachability from a guest is not verified.**
- **Readings contract**: `box1.telemetry.events.v1`, 6 partitions, 2 days retention (`platform/kafka/topics/telemetry.yaml`). `TELEMETRY.md` keys it by **`assetId`** and derives `eventId` from `(assetId, metricName, measuredAt)`.
- **The issue says every event is keyed by `siteId`.** That conflicts with the readings contract. Site events go to the new site topic from `01`, keyed by `siteId`.
- **Outbox precedent**: `inventory-service` `V1__inventory_schema.sql` L114–133 and `messaging/OutboxPublisher.java` (scheduled, key = `aggregateId` at L181–183). `asset-service` publishes readings directly with no outbox; only its threshold events use one (`OutboxRelay.java`).
- **Fixture assets** (`scenario-controller` `Fixtures.java` L45–47): `asset_replicator_spacedock` (temperature) at `site_spacedock`, `asset_litterbox_transporter_ds9` (vibration) at `site_ds9`.
- Envelope and trace context: see `01_DOMAIN_CONTRACTS.md` and `box1-ops-contracts/events/v1/envelope.schema.json`.

## Decided design

From the issue and #126's decisions.

**Simulator (`simulator` module)**
- Seeded and deterministic; publishes readings for the site's fixture assets over MQTT to the local AMQ Broker. The seed and rate come from configuration; `siteId` comes from `/etc/box1/site.env`.

**Forwarder (`gateway` module, Camel Quarkus)**
- Consumes MQTT. For each reading or site event it writes one outbox row in a PostgreSQL transaction, with Flyway-managed schema, following the cluster services' outbox pattern.
- MQTT delivery to the forwarder is at least once (QoS 1). The outbox insert is idempotent on `eventId`.
- Each event has an `eventId`, W3C trace context and its original `occurredAt` (and `measuredAt` for readings). Readings derive `eventId` as `TELEMETRY.md` says, so a re-sent reading has the same `eventId`.
- Site events from `site-ops` (`06`) are written into the same outbox; the forwarder does not need to understand them.

**Publisher**
- Drains the outbox in order, with idempotent producer settings and `acks=all`, and marks a row published only after the broker acknowledges it.
- Readings: `equipment.reading.v1` on `box1.telemetry.events.v1`. Site events: the `site.*.v1` family on the site topic, keyed by `siteId`.
- Bounded retries with backoff while Kafka is unreachable; no busy loop.

**Bounded buffer**
- A stated maximum row count or byte size and a maximum age, chosen from the measured data rate and the site's storage.
- A documented overflow policy. Recommended: readings are dropped oldest first with a counted, logged drop, while site events (picks, counts, holds) are never dropped and instead apply backpressure to `site-ops`. Record the decision.
- Buffer depth, oldest-row age, drops and publish rate are Micrometer metrics, and the depth is available to the site agent (`04`).

## Scope and guardrails

**In scope**
- `site-gateway` modules `simulator` and `gateway`: code, Flyway migrations, tests (Testcontainers or Dev Services for Kafka, PostgreSQL and an MQTT broker).
- Configuration consumed from `/etc/box1/site.env`.
- The `site-gateway-os` changes these modules need (unit environment, ports), through that repository's PR path.
- A runbook section for draining and replaying the buffer.

**Out of scope**
- asset-service ingestion (`05`), inventory consumption (`06`), the site agent heartbeat (`04`), Kafka authentication (#71, `03`).
- Changing the readings key or topic of `box1.telemetry.events.v1`. If the owner wants readings keyed by `siteId`, that is a breaking contract change and a stop condition.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #127 only with the evidence named.

- [ ] Readings and site events from both sites arrive on Kafka with `siteId`, `eventId`, `occurredAt` and trace context, and validate against the contracts.
  - Evidence: `kafka-console-consumer` samples from both topics for both sites (headers and key), validated with `box1-ops-contracts` `scripts/validate.mjs` or an equivalent test.
- [ ] With the site's NIC detached, events accumulate in the outbox. The buffer stays within its stated bound, and the overflow policy behaves as documented.
  - Evidence: the approved NIC detach on one site, outbox depth and age over time from the guest, the bound and policy as written, and an overflow run (shrunken bound in a test is acceptable if stated).
- [ ] After reconnection, the backlog drains, and site-side counts match what was published: no loss and no duplicates.
  - Evidence: site-side counts by type and `eventId` set, Kafka counts for the same window (distinct and total), and the drain time.
- [ ] Killing site-gateway or rebooting the VM mid-drain loses nothing that had been committed to the outbox.
  - Evidence: `systemctl kill` and a VM reboot during a drain (approval), then the same count comparison.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/127-site-forwarder/`.

**Discovery must cover**
- The `site-gateway` repository and bundle path from #137, and the `site-gateway-os` units from `01`.
- The merged contracts and site topic.
- Guest reachability of the Kafka bootstrap Service and the broker's advertised address.
- The data rate the simulator produces, to size the buffer.
- Whether #71 has changed the listener.

**Design decisions to record**
- Buffer bounds and overflow policy.
- MQTT topic layout and QoS.
- Outbox schema and claim strategy (single publisher; ordering per key).
- Producer settings (idempotence, `acks`, `delivery.timeout.ms`, retries).
- Metric names.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 2 Contracts | Every produced event validates against the pinned contracts commit |
| 4 Verification | Broker-down, overflow and crash-mid-drain scenarios pass locally |
| 6 Delivery | Bundle digest promoted into `site-gateway-os`, and that OS digest on both sites |
| 7 Live acceptance | All four criteria, with the approved faults |

**Verification scenarios**
- Kafka down for longer than the publisher's retry window.
- Duplicate MQTT delivery of the same reading.
- Outbox full: readings dropped as documented; site events backpressure.
- Crash between Kafka acknowledgement and marking the row published: the duplicate is harmless downstream (same `eventId`).
- PostgreSQL restart while the forwarder runs.
- Clock skew on the site: `occurredAt` keeps site time and is documented.

**Stop conditions**
- A guest cannot reach Kafka on the pod network and no listener change is approved.
- The owner requires a different key for readings.
- The contracts from `01` are not merged.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the bundle and OS digests carrying this code, on each site;
- buffer bounds, overflow policy and metric names (consumed by `04` and `07`);
- the drain and replay runbook section;
- evidence of the four criteria;
- rollback: promote the previous `site-gateway-os` digest; outbox rows are kept and drained by either version only if the migration is backward compatible (state whether it is).

Tick the completed items on #127.
