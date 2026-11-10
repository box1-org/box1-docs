# Local and CI test evidence (2026-11-10, America/New_York)

## box1-ops-contracts (branch edge-sites/126-site-contracts, 5b7296c)
- `npm test`: pass 79, fail 0 (new: site contract; eventId test vector).
- `npm run validate`: PASS 16 event fixtures, 16 schemas and 24 OpenAPI examples. An invalid site status example and
  an invalid count fixture were each rejected before being reverted.

## site-gateway (merged 44f35b7; commits 1e0671b, 1d0eb0f)
- `./mvnw -B verify` (as CI): gateway 22, ops 10, simulator 9 tests; 0 Checkstyle violations; SpotBugs/FindSecBugs
  0 findings per module.
- `./mvnw -B -pl gateway verify -Pcontainers` (Podman; PostgreSQL 16, Kafka 4.2.1, ActiveMQ Artemis 2.42.0): 31 tests,
  0 failures. Covers: MQTT → outbox → Kafka with a duplicate MQTT message (one record, valid envelope, key assetId,
  header box1-site-id, trace continued); Kafka paused, 20 readings buffered then drained exactly once; PostgreSQL
  paused, reading held then stored; broker backlog after a reconnect; pick list keeps only its site, early shipment
  closure, NUL record skipped; pick idempotency (201, replay 200, 409) and its site event on box1.site.events.v1
  (key site_ds9, causation = reservation eventId); readings bound drops the oldest 3 of 8 and records it; third site
  event refused with 503; crash between Kafka ack and commit re-sends 7 rows with the same eventIds.
- PR CI: site-gateway-validate-9nsnp (1e0671b) and site-gateway-validate-n8gcm (1d0eb0f) Succeeded.
- Release site-gateway-release-vptwg Succeeded: bundle
  `box1-ci/site-gateway-bundle@sha256:26543a45360ae49f3d48db695d3973551b39a2b4429c82ba8c2f6351da33e102`,
  gate-policy pass, scan 0 critical/high/medium/low, consumer PR box1-org/site-gateway-os#7 opened.

## site-gateway-os (PR #6)
- Probe builds (PR CI, nothing pushed): RHEL 10 AppStream has java-21-openjdk-headless 21.0.13, greenboot 0.16.3,
  greenboot-default-health-checks 0.16.3, opentelemetry-collector 0.158.0; podman 5.8.2 is in rhel-bootc:10.2.
  Installing the collector with its scriptlets made the later `setsebool -P` fail (site-gateway-os-validate-nnkxq).
- PR builds, each fixing what the previous one found: zdmfq (broker JVM: `-Xms512M` above `-Xmx384M`), jgtk8 (collector
  config not valid YAML; `StartLimitIntervalSec` in `[Service]`), qc4wb (filter needs `log.body`), gtrj2 (`file_storage`
  directory must exist for `validate`), v7l4s (Succeeded; JVM perf data left in `/tmp`).
- **site-gateway-os-validate-6pqnz Succeeded** on `36b9114`: broker stage MQTT up after 6 s (acceptors `artemis`
  61616 inside the container, `mqtt` 1883); quadlet units generated; `systemd-analyze verify` clean for the site
  units; `opentelemetry-collector validate` passes; `bootc container lint` 11 passed, 2 warnings that main also has
  (cloud-init `/run/cloud-init`, `/var/lib/cloud`). Image built and linted, not pushed.

## Subagent PRs (their own reports; not re-run here)
- asset-service#8: `./mvnw -B verify` 74 tests; `-Pcontainers` 94 tests, 0 failures.
- inventory-service#7: `./mvnw -B clean verify` 46 tests; containers suite 107 + 10 IT, 0 failures.
- operations-console#17: `./mvnw -B verify -DskipITs=false` 93 + 5 IT; Playwright e2e 25 passed.
