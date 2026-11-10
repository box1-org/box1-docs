# Checkpoint: edge sites #126–#133 (2026-11-10, America/New_York)

**Phase.** Implementation and local verification are complete for #127–#133 within what can be done without
approvals. site-gateway is merged and released. Every other change is an open PR for the owner. Nothing runs on a
site yet; no acceptance criterion is live-verified.

## Where everything is

| Repository | PR | State | What merging does |
|---|---|---|---|
| box1-ops-contracts | [#14](https://github.com/box1-org/box1-ops-contracts/pull/14) `5b7296c` | open | nothing deploys; consumers pin `5b7296c` (do not rebase or squash before they repin) |
| site-gateway | [#1](https://github.com/box1-org/site-gateway/pull/1) | **merged** `44f35b7` | released: bundle `sha256:26543a45…e102`, gate pass, opened site-gateway-os#7 |
| site-gateway-os | [#7](https://github.com/box1-org/site-gateway-os/pull/7) | open (release-generated) | bumps the bundle digest; release builds the OS and promotes it to the `site-gateway-os` VM |
| site-gateway-os | [#6](https://github.com/box1-org/site-gateway-os/pull/6) `36b9114` | open, PR build pass | the site units, quadlets, greenboot checks, collector; same release path |
| box1-workloads-dev | [#225](https://github.com/box1-org/box1-workloads-dev/pull/225) | open | Argo imports the AMQ Broker and PostgreSQL mirrors into `box1-ci` |
| box1-gitops | [#150](https://github.com/box1-org/box1-gitops/pull/150) | open | KafkaTopics `box1.site.events.v1`, `box1.site.dlq.v1` (manual sync of `box1-kafka`) |
| box1-gitops | [#151](https://github.com/box1-org/box1-gitops/pull/151) | open | Keycloak: `site-reporter` role, `siteId` claim on `site-west`/`site-east` (auto sync) |
| asset-service | [#8](https://github.com/box1-org/asset-service/pull/8) | open, CI pass | site status API, V2 migration, site metrics, generator guard (release + dev promotion) |
| box1-workloads-dev | [#223](https://github.com/box1-org/box1-workloads-dev/pull/223) | open | `Box1SiteStale` PrometheusRule (after asset-service#8 is deployed) |
| inventory-service | [#7](https://github.com/box1-org/inventory-service/pull/7) | open, CI pass | site-event consumer, V4 migration (additive, shared dev DB) |
| operations-console | [#17](https://github.com/box1-org/operations-console/pull/17) | open, CI pass | Sites map and status table |
| box1-gitops | [#152](https://github.com/box1-org/box1-gitops/pull/152) | open | box1-collector logs → LokiStack, metrics → Prometheus (manual sync; validate the config with the collector image first) |

## Suggested merge order (about 10 s apart, #64)

1. box1-ops-contracts#14.
2. box1-gitops#150 (topics), then sync `box1-kafka`; box1-workloads-dev#225 (image mirrors).
3. box1-gitops#151 (Keycloak); check a decoded site token (`azp`, `aud`, `siteId`, roles only).
4. asset-service#8, then box1-workloads-dev#223.
5. inventory-service#7.
6. operations-console#17.
7. site-gateway-os#7, then site-gateway-os#6 (each release promotes the source VM `site-gateway-os`).
8. Instance promotion of `site-east` then `site-west` to the new OS digest (#141 mechanism).
9. box1-gitops#152 after validating its config.

Site credentials: the Keycloak client secrets reach each VM through the #140 assembly flow (manual, approved).

## Exact next actions

- After the merges: boot evidence from `site-east` (`bootc status`, `systemctl status site-gateway-os.target`,
  `podman ps`, readiness, `/run/box1/site-facts.json`), then the #127–#133 acceptance runs; each fault injection
  (NIC detach, bad release, reboot, replay) needs approval.
- Not started: egress NetworkPolicy (D-006), Kafka identity (#71), agentic-operations site tool.

## Open risks

- `box1-ops-contracts` `5b7296c` is pinned from an unmerged branch.
- The site VMs reach asset-service and Keycloak through public Routes; reachability from a guest is not verified.
- greenboot rollback, the collector's OTLP paths and LokiStack OTLP ingestion are untested.
- Broker inside its container also has the default core acceptor on 61616 (not published outside the container).
