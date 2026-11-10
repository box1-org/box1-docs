# Edge sites onboarded: site-gateway, site-gateway-os, site-west and site-east

**Date:** 2026-11-09 21:00 EST to 2026-11-10 01:30 EST (America/New_York)

**Status:** Both edge-site VMs are running and verified, and both onboarding records are `COMPLETE`. This delivers the "site software" and "sites" work items of the Site Expansion epic [#126](https://github.com/box1-org/box1-docs/issues/126). #126 stays open: the site applications, integrations and drills (#127–#133, #141) are separate work in progress, and the site namespaces have no egress NetworkPolicy yet.

The golden paths used here are described in [2026-11-09 Site Expansion golden path](2026-11-09-site-expansion-golden-path.md).

## Outcome

Two RHEL 10 image-mode VMs now run as edge sites. Both were created from Developer Hub and both boot the same approved OS digest:

| | `site-west` | `site-east` |
|---|---|---|
| Fixture site | `site_ds9` | `site_spacedock` |
| Namespace | `site-west-dev` | `site-east-dev` |
| OS image (approved and booted) | `site-gateway-os@sha256:89e044b3…` | same |
| Keycloak client | `site-west` | `site-east` |
| Onboarding / promotion PRs (box1-workloads-dev) | [#220](https://github.com/box1-org/box1-workloads-dev/pull/220) / [#221](https://github.com/box1-org/box1-workloads-dev/pull/221) | [#222](https://github.com/box1-org/box1-workloads-dev/pull/222) / [#224](https://github.com/box1-org/box1-workloads-dev/pull/224) |
| Onboarding `COMPLETE` | 2026-11-10 00:30 EST | 2026-11-10 00:52 EST |

The OS image is built from `site-gateway-os`. It contains the site applications bundle from `site-gateway`, copied in by digest to `/usr/lib/box1/site-gateway/`. Each guest gets its identity from cloud-init: `/etc/box1/site.env`, plus a Keycloak client secret that only the `box1-site` service user can read.

The bundle hand-off now runs end to end:
1. A `site-gateway` merge (`44f35b7`) triggered release `site-gateway-release-vptwg`.
2. The release published `site-gateway-bundle@sha256:26543a45…`.
3. The security gate passed in `gate` mode, with 0 vulnerabilities.
4. The `box1-pipelines` App opened the digest-bump PR [site-gateway-os#7](https://github.com/box1-org/site-gateway-os/pull/7). The PR changes only the bundle `COPY` line.

## Starting baseline

- **Plugin and templates:** onboarding plugin 1.5.0 was released with the new templates on 2026-11-09. None of the new paths had been used live.
- **Resources:** no `site-*` repositories, workloads, Keycloak clients or credentials existed.
- **Capacity:** two instances were checked read-only before provisioning. Memory was the tightest resource, and two 2-vCPU / 4Gi VMs fit (run state in `agent-runs/138-vm-instance/`).

## What was created

| Item | How | Evidence |
|---|---|---|
| `site-gateway` (`artifact`) | The owner used **Create Quarkus Multi-Module Repository**, modules `gateway`, `ops`, `simulator` | Record `COMPLETE` 21:26 EST. No `site-gateway-dev` namespace, Deployment or workload Application, only `site-gateway-ci`. PR check `site-gateway-validate-*`: reactor `SUCCESS` for every module |
| `site-gateway-os` (`virtual-machine`, cloud-init on) | **Create RHEL 10 Image Mode VM** | Record `COMPLETE` 21:09 EST ([box1-workloads-dev#201](https://github.com/box1-org/box1-workloads-dev/pull/201), [#203](https://github.com/box1-org/box1-workloads-dev/pull/203)) |
| Keycloak clients `site-west`, `site-east` | [box1-gitops#146](https://github.com/box1-org/box1-gitops/pull/146). Confidential, client credentials only; tokens carry `aud: asset-service` and `site_id` | Real token requests returned the expected `aud` and `site_id`. A wrong secret and a password grant both got `401 unauthorized_client` |
| `<site>-cloud-init` Secrets | Approved. `scripts/vm-cloud-init/assemble_cloud_init_secret.py` (box1-docs#147) ran plan → server dry-run → apply | Credential matches the Keycloak secret by SHA-256. No local copy kept; nothing printed |
| `box1-ci/vm-instance-status-ssh` | Approved. An ed25519 key generated locally and stored as an `ssh-auth` Secret; the local private key was deleted | Fingerprint `SHA256:o3i07lRy…`, matching the public key baked into `site-gateway-os` |
| `site-west`, `site-east` | **Add a VM Instance (Site) of an OS Image**, using the inputs in `agent-runs/138-vm-instance/site-inputs.md` | See **Validation** |

## Problems found on the way, and their fixes

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `site-gateway-os` release failed on `COPY --from=…: no stage or image found` | The `COPY` line was incomplete; the build had no registry login | Corrected line ([site-gateway-os#1](https://github.com/box1-org/site-gateway-os/pull/1)); route login, then a pull account for PR builds ([box1-gitops#140](https://github.com/box1-org/box1-gitops/pull/140), [#141](https://github.com/box1-org/box1-gitops/pull/141)). A pull Role added along the way was unnecessary and was removed (#143, #209) |
| 2 | The release run for #1's merge was stranded `PipelineRunPending`; a GitHub **Re-run** matched no PipelineRun | Known PaC start-time 404 ([#64](https://github.com/box1-org/box1-docs/issues/64)) | Cancelled the orphans; empty-commit PR [site-gateway-os#2](https://github.com/box1-org/site-gateway-os/pull/2) |
| 3 | `site-west` catalog step: "Existing catalog entity … is not this VM instance" | `blob/` vs `tree/` location comparison | Plugin 1.5.1 |
| 4 | `site-west`'s booted-digest check could not run | No `box1-status` guest user and no key Secret | `box1-status` with a forced `bootc status` command ([site-gateway-os#3](https://github.com/box1-org/site-gateway-os/pull/3)); key Secret created |
| 5 | The recreated `site-west` waited forever at sync | Plugin 1.5.1 adopted the earlier onboarding's merged PR #210 | Plugin 1.5.2 |
| 6 | Booted-digest SSH as `box1-status` exited 255 | `sshd` refused the key: "bad ownership or modes for directory /usr/share/box1" (775 from the CI build context) | Directory modes fixed, with a build check for the whole path ([site-gateway-os#4](https://github.com/box1-org/site-gateway-os/pull/4), [#5](https://github.com/box1-org/site-gateway-os/pull/5)) |
| 7 | `site-east` failed with `fetch failed` | GitHub was unreachable from the cluster and a workstation for a few minutes (about 00:39 EST); GitHub status showed no incident | Resubmitted; the run resumed from its record |
| 8 | `site-east`'s promotion checks stayed queued | A `box1-workloads-dev` run finished during the outage, kept PaC `state: started`, and blocked the concurrency-1 queue | The owner annotated the finished run, which re-triggered the watcher; recorded on #64 |

Problems 4 and 6 each needed a new `site-gateway-os` image, and an instance's onboarding record pins the digest it adopted. So `site-west` was decommissioned and recreated twice with the vm-instance runbook ([box1-workloads-dev#215](https://github.com/box1-org/box1-workloads-dev/pull/215), [#218](https://github.com/box1-org/box1-workloads-dev/pull/218)). Each time:
- The Application was removed with the resources finalizer, and the Hub records were cleared.
- The source `site-gateway-os`, its image streams and its Application stayed Synced/Healthy.

After onboarding, `site-gateway-os` had four release runs:

| Run | Result | Approved digest |
|---|---|---|
| `smtx9` | succeeded | `82b0badb` |
| `q9vw6` | succeeded | `a11d6786` |
| `swjk6` | failed on #4's new permission check; fixed by #5 | — |
| `65p6q` | succeeded | `89e044b3` |

## Validation and evidence

- **Onboarding checks.** Both onboarding records are `COMPLETE`. The plugin's booted-digest check (`onb-<site>-boot-89e044b3`, run as `box1-status` through `box1-bootc-status`) confirmed `89e044b3…` on each site.
- **In each guest,** checked with `virtctl ssh` as `cloud-user`:
  - `bootc status` reports `sha256:89e044b3…`;
  - `/etc/box1/site.env` has `BOX1_SITE_ID=site_ds9` on `site-west` and `site_spacedock` on `site-east`;
  - the credential file is `box1-site:box1-site 400`, and `sudo -u cloud-user test -r` fails;
  - `/usr/share/box1` is `drwxr-xr-x`.
- **Cluster state.**
  - VMIs are `Ready`, `AgentConnected` and `AccessCredentialsSynchronized`.
  - The `site-west` and `site-east` Applications are Synced/Healthy.
  - The VM manifests carry only `cloudInitNoCloud.secretRef`, with no `userData`.
- **Existing VMs:** `legacy-erp` and `vm-golden-check` are still `Running` on the digests recorded before #140, with no cloud-init volume.

**Not tested:**
- promoting one instance without the other;
- re-creating a VM while keeping a data disk (instances have none yet);
- a policy-failing bundle;
- decommissioning an instance while another instance exists.

## Final operational state

| Resource | State | Managed by |
|---|---|---|
| `site-west`, `site-east` | VMs Running on `89e044b3…` | Argo CD (`box1-workloads-dev`); onboarding records in `rhdh` |
| `site-gateway-os` | Approved `89e044b3…` at `9fe5ba4`. Its own reference VM runs in `site-gateway-os-dev` | Argo CD; releases by PaC |
| `site-gateway` | Bundle `26543a45…` released; bump PR site-gateway-os#7 open | PaC through `ci/site-gateway` |
| Keycloak clients | `site-west`, `site-east` | Argo CD `keycloak` (`prune: false`) |
| Cloud-init Secrets, status key | Outside Git | Recreate with the #147 runbook, or a new key pair |

Plugin 1.5.2 (`sha256:209cbf816c…`) is pinned in `box1-gitops`.

**Leftovers and differences from `main`:**
- The failed run `onb-site-west-boot-a11d6786` is still in `box1-ci`. It's harmless and can be deleted.
- A site's root disk is not swapped on day-2 promotion. An instance stays on its adopted digest until it is recreated, or until #141 adds in-guest upgrades.

## Recovery and follow-ups

**Back-out point:**
- The annotated tags `pre-site-expansion-2026-11-09` are on box1-templates `5663eb3`, box1-gitops `8e298a6`, box1-workloads-dev `937ccb3` and box1-docs `757a28a`. Each is the last `main` commit before #126 was filed.
- The procedure is [runbooks/site-expansion-backout.md](../../runbooks/site-expansion-backout.md) ([#158](https://github.com/box1-org/box1-docs/pull/158)), in three cumulative levels: sites; site software; golden path. Don't reset `main` to the tags, because unrelated work landed afterwards.
- The Git revert sets were dry-run cleanly. The cluster steps have not been run.

**To remove one site:** follow [service decommission](../../runbooks/service-decommission.md), vm-instance section. Then delete its KeycloakClient by hand, because the `keycloak` Application doesn't prune.

**Follow-ups:**
- [#157](https://github.com/box1-org/box1-docs/issues/157): plugin retries on transient network errors.
- [#64](https://github.com/box1-org/box1-docs/issues/64): new stranding modes and the annotate recovery.
- [#141](https://github.com/box1-org/box1-docs/issues/141): staged per-site OS rollout.
- The egress NetworkPolicy for site namespaces (#126).
- Per-VM resource measurements (#126).
- The remaining live criteria on #136–#140.
