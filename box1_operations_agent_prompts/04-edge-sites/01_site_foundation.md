# Edge sites 01 — Site foundation: contracts and the `site-gateway-os` image

> **This is the first edge-sites prompt.** It lays the shared ground the other edge-sites prompts build on: the `site.*.v1` contracts and the site status API in `box1-ops-contracts`, and the `site-gateway-os` RHEL 10 bootc image that runs the site apps, AMQ Broker and PostgreSQL. Read `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Creating a repository, running onboarding, merging to `main` and merging contracts or GitOps changes all need approval.
- The user merges. Wait about 10 seconds between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- No credential goes in Git, the image, logs or evidence.
- Do not touch `legacy-erp`, `vm-golden-check` or other VMs.
- Put test materials and evidence in `box1-docs`, not `box1-gitops`.
- Do not use Chrome.

**Issue:** [box1-docs#126](https://github.com/box1-org/box1-docs/issues/126) (epic), the work items "Contracts" and "`site-gateway-os` created from the `rhel-image-vm` template". The epic's closing items are `09_edge_sites_acceptance.md`.

**Dependencies**
- [#140](https://github.com/box1-org/box1-docs/issues/140) (`../03-golden-path/03_vm_cloud_init_nocloud.md`): the `rhel-image-vm` cloud-init parameter must be merged before `site-gateway-os` is created, so the image reads `/etc/box1/site.env`.
- [#136](https://github.com/box1-org/box1-docs/issues/136) (`../03-golden-path/01_onboarding_profile_dispatch.md`): the released plugin, because onboarding runs through it.
- [#137](https://github.com/box1-org/box1-docs/issues/137) (`../03-golden-path/04_artifact_profile_quarkus_monorepo.md`) creates `site-gateway` and needs `site-gateway-os` as its consumer. This prompt creates the consumer first and agrees the bundle layout with that run.
- [#138](https://github.com/box1-org/box1-docs/issues/138) (`../03-golden-path/05_vm_instance_profile_template.md`) needs an approved `site-gateway-os-disk` digest from this prompt, and creates `site-west` and `site-east`.

## Mission

Make "a site" a real operating environment that the later prompts can fill in:
1. Add the `site.*.v1` event family and the asset-service site status API to `box1-ops-contracts`, and confirm `EquipmentReading.v1` covers what a site sends.
2. Create `site-gateway-os` from the `rhel-image-vm` template through Developer Hub, with cloud-init on, the Java runtime, systemd units for the three site apps, AMQ Broker (MQTT) and PostgreSQL as digest-pinned Podman quadlets, and persistent site data.
3. Produce an approved `site-gateway-os-disk` digest that #138 can boot as `site-west` (`site_ds9`) and `site-east` (`site_spacedock`).

## Verified baseline (observed 2026-11-09; verify before relying)

**Golden-path state.** The golden-path code merged on 2026-11-09: `box1-templates#33`–`#37` (profile dispatch, cloud-init, `quarkus-monorepo`, `vm-instance`) and `box1-gitops#132`–`#134` and `#136` (validate and promote for `vm-instance`, bundle Tasks, `box1-bootc-status`, onboarding plugin 1.5.0). Issues #136–#140 are still open, their run-state PRs ([#145](https://github.com/box1-org/box1-docs/pull/145)–[#148](https://github.com/box1-org/box1-docs/pull/148), [#150](https://github.com/box1-org/box1-docs/pull/150)) are unmerged, and nothing is live-verified. `site-gateway` and `site-gateway-os` do not exist (404).

**Guest contracts `site-gateway-os` must provide**, from the merged golden path:
- user `box1-status`, with its key forced to `sudo /usr/bin/bootc status --format json`, for `box1-bootc-status` (`box1-gitops/platform/pipelines/GOLDEN-PATH.md`, "Booted-digest check");
- the digest-pinned switch user and wrapper that `../03-golden-path/06_staged_site_rollout.md` (#141) defines;
- cloud-init on, reading `/etc/box1/site.env`. The `vm-instance` template's `<instance>-site` ConfigMap carries `siteId`, the Keycloak client ID and token URL, and optional asset-service URL, Kafka bootstrap and OTLP endpoint.

**A repository created from `rhel-image-vm` also gets its own VM** (`<source>` in `<source>-dev`, promoted by its release pipeline). For `site-gateway-os` that is a third VM, unless it is excluded; decide with #141.

**Contracts** (`box1-ops-contracts` main `7b7fbac5`)
- Envelope (`events/v1/envelope.schema.json` L7–18): `eventId` (uuid), `eventType`, `schemaVersion` (const 1), `aggregateId`, `occurredAt`, `correlationId`, `causationId`, `payload` are required; `traceparent`, `tracestate` are optional.
- The `eventType` pattern (L10) allows exactly two dot segments plus `.vN`. `site.pick-confirmed.v1` is valid; `site.pick.confirmed.v1` is not.
- `equipment.reading.schema.json` L7–15 is closed: `assetId`, `siteId`, `measuredAt`, `metricName`, `value`, `unit`. `eventId`, `occurredAt` and trace context are envelope fields.
- `TELEMETRY.md` L7–14: topic `box1.telemetry.events.v1`, **keyed by `assetId`**; `eventId` is derived from `(assetId, metricName, measuredAt)`; `causationId` is `ingest:api|load|chaos`.
- `inventory.reserved.v1`: `orderId`, `reservationId`, `sku`, `quantity`, `siteId`, `expiresAt` (one SKU per reservation).
- There are no `site.*`, `PickConfirmed` or `StockAdjusted` schemas, no site topic, and no `/sites` paths in the asset OpenAPI.
- `TOPICS.md` L3–14 names topics `box1.<domain>.events.v1` and `box1.<domain>.dlq.v1`; L20 requires new consumer groups to be declared there first.
- `scripts/validate.mjs` L14–18 finds a payload schema by stripping `.vN` from `eventType`; a new event needs `site.<name>.schema.json` and a fixture in `fixtures/events.json`. `test/contracts.test.mjs` L9 hard-codes the schema list.
- **The repository has no CI and `main` is unprotected.** Services pin a contracts commit (asset-service `pom.xml` L21 `2fe191dc…`, inventory-service `pom.xml` L21 `85d72e3c…`), so consumers bump the ref themselves.

**Fixture sites** are not in the contracts repository. The canonical set is `scenario-controller` `src/main/java/org/box1/scenario/fixtures/Fixtures.java`: sites L21–25 (`site_spacedock`, `site_ds9`, `site_utopia_planitia`, `site_neutral_zone` UNAVAILABLE), assets L45–47 (`asset_replicator_spacedock` temperature, `asset_litterbox_transporter_ds9` vibration), stock L51–64.

**The VM template** (`box1-templates` main `5663eb3`, `templates/rhel-image-vm`)
- `skeleton/Containerfile`: `FROM registry.redhat.io/rhel10/rhel-bootc:10.2@sha256:80485ddb…` (L6); one `dnf install` from the RHEL CDN with entitlement build secrets (L16–23); default target `<name>.target`, `box1-registry-setup.service` enabled, `bootc-fetch-apply-updates.timer` disabled, `bootc container lint` (L29–38).
- The example unit `<name>-heartbeat.service` uses `DynamicUser` and `ProtectSystem=strict`.
- The VM uses the pod network with `masquerade` (`gitops/workloads/<name>/virtualmachine.yaml` L56–61). The guest has resolved `image-registry.openshift-image-registry.svc`; reaching other Services from a guest is **not verified**.
- The VM bundle has one root DataVolume; there is no data disk.

**Precedent: `legacy-erp`** (main `9f51971`): multistage Containerfile, units in `/usr/lib/systemd/system` (L51–61), a single `semanage import` transaction (a second one in the same layer fails on cluster buildah, L69–72), `systemd-analyze verify` (L92). A `box1-deploy` user is limited by sudoers to `bootc upgrade --apply` and `bootc status --format json`.

**Nothing in any `box1-org` repository uses Podman quadlets, AMQ Broker, `rhel10/postgresql` or greenboot.** The existing PostgreSQL precedent is `registry.redhat.io/rhel9/postgresql-15@sha256:95e94264…` (for example `box1-workloads-dev/workloads/asset-service/postgres.yaml` L47).

**Capacity** ([2026-11-06 PV capacity audit](https://github.com/box1-org/box1-docs/blob/main/achievements/2026/2026-11-06-pv-capacity-audit.md)): reservable thin-pool capacity was 786 GiB after `overprovisionRatio` was raised to 2 by a manual `oc patch` that Argo does not manage. The audit has no CPU or memory figures; on 2026-11-06 about 75% of CPU and 70% of memory were already requested. The epic's estimate, not measured, is 2 vCPU, 4 GiB RAM, a 20 GiB root disk and a 5 GiB data disk per site.

## Decided design

From #126's two decision comments (2026-11-08) and the #137 and #140 decisions.

**Contracts (one `box1-ops-contracts` PR)**
- Site events, at least: `site.pick-confirmed.v1`, `site.stock-adjusted.v1` (cycle count) and `site.stock-held.v1` (hold placed or released). Each carries `siteId`, the site-local identifiers needed for idempotency, and the time it happened at the site. Agree field semantics with `06_site_pick_lists_reconciliation.md` before merging; a later breaking change needs a new version.
- A site topic, proposed `box1.site.events.v1` keyed by `siteId`, with a DLQ `box1.site.dlq.v1`, documented in `TOPICS.md`. Creating the KafkaTopics is a shared-infrastructure GitOps PR that needs approval.
- The asset-service site status API in `openapi/`: `PUT /api/v1/sites/{siteId}/status` (heartbeat: time, buffer depth, booted OS digest, greenboot status, app versions) and `GET /api/v1/sites`, `GET /api/v1/sites/{siteId}`, with the online, degraded and offline states.
- Readings stay `equipment.reading.v1`. Site-gateway derives `eventId` exactly as `TELEMETRY.md` says, so a replayed reading has the same `eventId`. Add a `causationId` value for site ingestion, proposed `ingest:site`.
- Add fixtures and tests for every new schema, and update the hard-coded list in `test/contracts.test.mjs`.

**`site-gateway-os` (created through Developer Hub from `rhel-image-vm`, cloud-init on)**
- Packages: `java-21-openjdk-headless`, `podman` (if not in the base), `cloud-init` (from #140) and anything the quadlets need, all in the single `dnf install`.
- The site apps: `COPY --from=<registry>/box1-ci/site-gateway-bundle@sha256:<digest>` into a fixed path, agreed with #137. Until the first bundle exists, use a placeholder bundle or a scratch stage and record it; #137's first digest-bump PR replaces it.
- systemd units for `site-gateway`, `site-ops` and `site-simulator`: non-root service user (agree its name with #140's credential owner), `EnvironmentFile=/etc/box1/site.env`, restart policy, and ordering after the broker and database.
- Quadlets in `/usr/share/containers/systemd/`: AMQ Broker with an MQTT acceptor, and PostgreSQL (`rhel10/postgresql-*` if available, otherwise record the fallback), each pinned by digest, bound to localhost, with data on persistent storage.
- **Persistent site data.** The outbox and broker data must survive reboots, `bootc upgrade` and rollback. `/var` persists across bootc deployments; a separate 5 GiB data disk would also survive a root-disk re-create, but #138's instance bundle has no data disk. Decide which, and if a data disk is chosen, agree the bundle change with #138 before it merges.
- A site target (for example `site-gateway.target`) as the default target, so `bootc-apply`'s `expected-units` check covers every site service.
- Image pull credentials for the quadlet images: the image must not contain a registry credential. Either mirror the images into `box1-ci` (preferred; the guest already has a registry token) or document an approved alternative.

## Scope and guardrails

**In scope**
- The contracts PR above.
- Creating `site-gateway-os` from Developer Hub (approval), its Containerfile, rootfs, units and quadlets, and its first gated release with an approved `-disk` digest.
- A test VM from that digest, in an approved namespace, to prove the image boots and the services start, unless #138 instances already exist.
- Measured idle RAM, CPU and disk for the image, which feed #126 and #138.

**Out of scope**
- `site-gateway` code and the bundle pipeline (#137, then `02`–`06`).
- `site-west` and `site-east` instances (#138).
- greenboot checks (#133, `08`), the in-guest collector (#132, `07`), Keycloak clients (#131, `03`).
- The egress NetworkPolicy (`09`).

## Verifiable acceptance evidence

These items are this prompt's share of #126's work items and acceptance criteria. Tick a #126 checklist item only with the evidence named.

- [ ] Contracts: the `site.*.v1` events, the site topic and the site status API are in `box1-ops-contracts`, and `EquipmentReading.v1` is confirmed to cover what the sites send.
  - Evidence: the merged PR, `npm test` and `npm run validate` output, and a note mapping each site event and heartbeat field to the issues that consume it (#127, #129, #130).
- [ ] `site-gateway-os` is created from the `rhel-image-vm` template, consuming the bundle by digest.
  - Evidence: the Hub task ID, the repository tree, the release PipelineRun, the gated image and `-disk` digests, and the `COPY --from=…@sha256:` line (placeholder recorded if #137 has not published yet).
- [ ] A VM booted from that digest starts the broker, the database and the three site units, and reads its identity from `/etc/box1/site.env`.
  - Evidence: `bootc status --format json`, `systemctl status` of the site target, `podman ps` with image digests, an MQTT connect test against the broker and a `psql` connect test, all from the guest.
- [ ] Site data persists across a reboot and a `bootc upgrade` to a trivial second digest.
  - Evidence: a marker row in PostgreSQL and a retained MQTT message (or broker journal file) before and after.
- [ ] Measured RAM, CPU and storage for the image are recorded, and LVMS headroom and node requests are checked.
  - Evidence: guest `free`, `df`, `systemd-cgtop` samples, the VM's requests, and `oc describe node` allocated resources.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/126-site-foundation/`.

**Discovery must cover**
- The merged state of #136, #137, #139 and #140, and the bundle layout #137 chose.
- `box1-ops-contracts` main, its consumers' pinned refs, and the fixture sites and assets in `scenario-controller`.
- Image availability with the cluster's pull secret: the AMQ Broker image with MQTT, `rhel10/postgresql-*`, and whether `rhel-bootc:10.2` already contains `podman` and `greenboot`.
- Whether a guest on the pod network can reach `box1-kafka-kafka-bootstrap.box1-kafka.svc:9092`, `asset-service` and `keycloak.apps.ocp.box1.org` (from a test VM).
- LVMS capacity, node CPU and memory requests.

**Design decisions to record**
- The site event names, fields and the site topic.
- `eventId` derivation for readings and site events.
- Persistent data: `/var` or a data disk (with #138).
- Quadlet image source and pull credentials.
- Service user, unit layout and the site target name.
- AMQ Broker MQTT configuration (acceptor, persistence, memory limits) and PostgreSQL version.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 0 Discovery | Golden-path dependencies merged; image availability and guest reachability tested, not assumed |
| 2 Contracts | Contracts PR merged with fixtures and tests; consumer ref bumps listed for `02`–`06` |
| 3 Implementation | `systemd-analyze verify` and `bootc container lint` pass in the image build |
| 6 Delivery | Release gated; `-disk` digest approved through the VM golden path |
| 7 Live acceptance | Boot, service and persistence evidence from a guest |

**Verification scenarios**
- The image boots without a NoCloud disk and the site units wait or fail clearly.
- PostgreSQL or the broker is stopped: dependent units do not report healthy.
- Reboot and `bootc upgrade`: data persists.
- `bootc rollback`: data persists and the previous units start.
- A missing quadlet image digest fails the build, not the boot.

**Stop conditions**
- #140 or #136 is not merged.
- No supported AMQ Broker or PostgreSQL image is pullable.
- A guest cannot reach Kafka or Keycloak through the pod network.
- Capacity is insufficient for two sites.
- The contract shape conflicts with what `06` needs and no owner decision is available.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the contracts commit and the ref each consumer must pin;
- the `site-gateway-os` repository, release, image and `-disk` digests;
- the bundle path agreed with #137 and the data-persistence decision handed to #138;
- measured resource use;
- rollback: revert the contracts PR before any consumer pins it; for the image, `bootc rollback` or re-promote the previous digest.

Tick the completed #126 work items.
