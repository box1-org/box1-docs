# Edge sites: disconnect and recovery, bad edge update, rebuild

Applies to the edge-site VMs of [#126](https://github.com/box1-org/box1-docs/issues/126): `site-west`
(`site_ds9`, namespace `site-west-dev`) and `site-east` (`site_spacedock`, `site-east-dev`). They run
[`box1-org/site-gateway-os`](https://github.com/box1-org/site-gateway-os), which carries the
[`box1-org/site-gateway`](https://github.com/box1-org/site-gateway) applications. Application-level operations
(buffer queries, replay, overflow, breach scenario) are in site-gateway's `docs/runbook.md`.

> **Status (2026-11-10).** Written from the implementation; none of these procedures has been run on the cluster
> yet. Every step that injects a fault (disconnect, bad release, rebuild, replay) needs the owner's approval, and
> only on the named site VMs. Never `legacy-erp` or `vm-golden-check`.

## What runs in a site

| Unit | Role | Listens |
|---|---|---|
| `site-broker.service` (quadlet) | AMQ Broker 7.14.1, MQTT only, data `/var/lib/box1-site/broker` | 127.0.0.1:1883 |
| `site-postgres.service` (quadlet) | PostgreSQL 16, data `/var/lib/box1-site/postgres` | 127.0.0.1:5432 |
| `site-gateway.service` | forwarder, outbox publisher, pick list, heartbeat | 127.0.0.1:8080 |
| `site-ops.service` | handheld pages | 127.0.0.1:8081 |
| `site-simulator.service` | equipment simulator | 127.0.0.1:8082 |
| `site-otel-collector.service` | journald, host and gateway metrics → `box1-collector` | — |
| `box1-site-facts.timer` | `/run/box1/site-facts.json` for the heartbeat | — |
| greenboot `required.d/{10,20,30,40}-site-*.sh` | health checks after each boot | — |

All of them run only when `/etc/box1/site.env` exists (cloud-init, `runbooks/vm-cloud-init-identity.md` from
[#147](https://github.com/box1-org/box1-docs/pull/147), not merged on 2026-11-10).

```sh
virtctl ssh -n site-west-dev cloud-user@vmi/site-west
sudo systemctl status site-gateway-os.target site-broker site-postgres site-gateway site-ops site-simulator
curl -s http://127.0.0.1:8080/q/health/ready; curl -s http://127.0.0.1:8080/api/v1/site/buffer
sudo cat /run/box1/site-facts.json
```

## Site goes dark (disconnect and recovery)

The demo control is a link cut, never a NetworkPolicy toggle (#126 decision).

**Method.** The VMs are Argo-managed with `selfHeal: true`, so changing the VirtualMachine's interface `state` to
`down` would be reverted by Argo; and no account has a console password. So the outage is scheduled inside the
guest before the link goes down, with its own end:

```sh
virtctl ssh -n site-west-dev cloud-user@vmi/site-west
IF=$(ip -o route show default | awk '{print $5}')            # the pod-network interface
date -u +%FT%TZ                                               # record the start
sudo systemd-run --unit=box1-drill-down --on-active=10s /usr/bin/nmcli device disconnect "$IF"
sudo systemd-run --unit=box1-drill-up --on-active=15min /usr/bin/nmcli device connect "$IF"
exit
```

To end early, there is no remote path while the link is down; wait for `box1-drill-up`, or restart the VM
(`virtctl restart`), which also restores the link.

**During the outage, expect:**
- the site keeps recording readings and operator actions; `site_outbox_depth` grows (seen after reconnect);
- asset-service shows the site `OFFLINE` after 90 s without a heartbeat; `Box1SiteStale` fires 180–240 s after the
  last heartbeat and reading; the other site stays `ONLINE`;
- the order flow is unaffected (inventory only, #129).

**After reconnection, check:**
1. `site_outbox_depth` returns to 0 and the site is `ONLINE` again; `Box1SiteStale` resolves.
2. Counts for the outage window, in the site database (site-gateway runbook "Buffer depth and a clean drain"):
   recorded = published + dropped, distinct `event_id` = rows.
3. The same window on Kafka by `eventId` (distinct and total) for `box1.telemetry.events.v1` and
   `box1.site.events.v1`; asset-service and inventory-service rows unchanged by duplicates.
4. Peak depth stayed within the bound (100 000 readings, 20 000 site events); `outbox_drop` empty unless overflow
   was the point of the drill.

## Bad edge update (greenboot rollback)

A release is one OS digest that contains the apps (`site-gateway-os` copies the `site-gateway` bundle by digest).
Releases reach `site-east` first and `site-west` only after `site-east` verifies (#141).

**Recognising a rollback:**
```sh
sudo journalctl -b -1 -u greenboot-healthcheck   # the failed boot's checks
sudo journalctl -b -u greenboot-healthcheck       # this boot
sudo bootc status                                 # booted is the previous digest; rollback holds the bad one
cat /run/box1/site-facts.json                     # what the heartbeat reports (bootedImageDigest, rollbackImageDigest, greenbootStatus)
```
greenboot reboots into the previous deployment after `GREENBOOT_MAX_BOOT_ATTEMPTS` (3) failed boots. The console
then shows the previous digest for the site; the stage's booted-digest check (#141) fails because booted ≠ approved,
which stops promotion to `site-west`.

**Reconciling.** Revert the instance's approved digest in `box1-workloads-dev` to the booted digest through the
promotion PR path (#141 decides the mechanism); never patch the VirtualMachine directly. Fix the release in
`site-gateway` or `site-gateway-os` and promote again from `site-east`.

**Data.** `/var/lib/box1-site` is not part of the deployment, so buffered rows survive the upgrade and the rollback.
Because a rollback runs the previous apps on the newer database schema, site-gateway migrations must be additive.

**Deliberately bad release for the drill (approval, `site-east` only).** For example a site-gateway change whose
readiness never reports UP; greenboot's `30-site-gateway.sh` fails after 300 s per boot.

## Rebuild and restore a site VM

A site is recreated from its `vm-instance` definition: the root DataVolume is imported again from
`box1-ci/site-gateway-os-disk` at the instance's approved digest, and cloud-init re-applies the identity from
`<instance>-cloud-init` (re-run the assembly script first if the Secret was deleted).

**What is lost:** everything under `/var` of the old root disk: buffered outbox rows not yet published, the
pick list (rebuilt from Kafka by replay of the retained topics, consumer group `site-gateway-<siteId>`; offsets are
kept by Kafka, so reset the group to `earliest` for a full rebuild), local holds and recent actions, and the broker's
queued MQTT messages. Check `site_outbox_depth` is 0 before a planned rebuild, so nothing unpublished is lost.

**What is kept:** the site's identity (Git ConfigMap and the out-of-Git Secret), its Keycloak client, central
inventory and telemetry.

Procedure: follow the `vm-instance` decommission and onboarding runbooks for the instance (#138), then check the
"What runs in a site" commands, the heartbeat (`ONLINE`), and a reading arriving in asset-service.
