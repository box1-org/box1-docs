# Box1 PV capacity audit — 2026-11-06

**Snapshot time:** evening of 2026-11-06, America/New_York (live OpenShift and LVM queries during this chat)
**Previous snapshot:** [2026-11-04 PV usage report](2026-11-04-pv-usage-report.md)

## Outcome

The LVMS thin pool is **about 22% written but 91% reserved**. Box1's storage problem is the allocation policy (`overprovisionRatio: 1`), not a full disk. Under that ratio every PVC reserves its full requested size at bind time. Only **78.5 GiB** is left to reserve, so new large claims are refused even though roughly 670 GiB of the pool has never been written.

Visible impact: the MTA hub cannot start. `openshift-mta/mta-hub-bucket-volume-claim` (100 Gi) is Pending with `NotEnoughCapacity`, and `mta-hub-database-volume-claim` (10 Gi) is waiting on the same unscheduled pod.

The audit itself was read-only. Afterwards, at the user's request, the overprovision ratio was raised from 1 to 2. That change unblocked MTA; see [Change applied: overprovisionRatio 1 → 2](#change-applied-overprovisionratio-1--2). Nothing was resized or deleted.

## Backend pool (new in this audit)

| Item | Value |
|---|---|
| Node | `quark.host.box1.org` (single node) |
| Device / VG | `/dev/nvme1n1` (931.5 GiB) → `vg1`, 931.51 GiB, 73.13 GiB VFree |
| Thin pool | `vg1/thin-pool-1`, 857.54 GiB (`sizePercent: 90`) |
| Thin pool Data% / Meta% | **21.74%** (~186 GiB written) / 11.06% |
| `thinPoolConfig.overprovisionRatio` | **1** |
| TopoLVM reservable capacity (`capacity.topolvm.io/vg1`) | **78.5 GiB** |
| LVMCluster | `ResourcesAvailable=True`, `VolumeGroupsReady=True`, state `Ready` |

The 11-04 report did not measure the backend pool. It listed this as a follow-up, and this audit closes it.

## PV inventory

| Scope | 2026-11-04 | 2026-11-06 |
|---|---:|---:|
| Bound PVs | 25 | 39 |
| Requested capacity, all modes | 829 GiB | **774 GiB** |
| Filesystem | 679 GiB | 560 GiB |
| Block (VM disks and OS images) | 150 GiB | 214 GiB |
| Pending PVCs | not recorded | 3 |

All PVs are `Bound`, use storage class `lvms-vg1` (TopoLVM, `WaitForFirstConsumer`), and have reclaim policy `Delete`. No `Released` or `Failed` PVs were found.

**Requested capacity fell even though the PV count rose.** The 150 Gi `vllm/vllm-model-cache` was replaced by a 65 Gi `vllm/vllm-models-cache` (20.9 GiB used). New since 11-04:

- Seven app Postgres PVCs at 5 Gi or 1 Gi each: asset, fulfillment-adapter, scenario-controller, demo-day, notification, order, and inventory services.
- The MTA Keycloak database (1 Gi), Tempo (10 Gi), Perses (1 Gi), and MailHog (1 Gi).
- Block VM disks for `legacy-erp` (20 + 2 Gi) and `vm-golden-check` (12 Gi).

### Pending PVCs

| PVC | Size | State |
|---|---:|---|
| `openshift-mta/mta-hub-bucket-volume-claim` | 100 Gi | `NotEnoughCapacity`. At the time of the event the node had 91.5 GiB free to reserve. |
| `openshift-mta/mta-hub-database-volume-claim` | 10 Gi | Waiting for `mta-hub` pod scheduling, which is blocked by the claim above |
| `openshift-virtualization-os-images/fedora-3c9d3f5c2fac` | 30 Gi, Block | DataVolume in `ImportScheduled` for 34 h. The PVC is waiting for its first consumer. Root cause **not established**. |

## Measured filesystem usage

Kubelet statistics covered 27 mounted filesystem PVCs: **91.6 GiB used of 538 GiB reported capacity (17%)**. On 11-04 the figure was 87.7 GiB used across 16 measured PVCs.

| Namespace / PVC | Used | Capacity | Use | Change since 11-04 |
|---|---:|---:|---:|---|
| `stackrox/scanner-v4-db` | 24.7 GiB | 39.9 GiB | **61.8%** | up from 22.6 GiB |
| `vllm/vllm-models-cache` | 20.9 GiB | 64.9 GiB | 32.2% | replaces the 150 Gi cache |
| `openshift-image-registry/image-registry-storage` | 18.9 GiB | 99.9 GiB | 19.0% | up from 4.5 GiB |
| `openshift-storage/noobaa-db-pg-cluster-1` | 6.8 GiB | 49.9 GiB | 13.6% | flat |
| `openshift-storage/noobaa-db-pg-cluster-2` | 6.8 GiB | 49.9 GiB | 13.6% | flat |
| `trusted-profile-analyzer/importer-8fcc46f77-kpch6-workdir` | 5.9 GiB | 7.9 GiB | **74.4%** | not measured on 11-04 |
| `trusted-profile-analyzer/postgres-data` | 2.8 GiB | 44.9 GiB | 6.1% | |
| `rhdh/dynamic-plugins-root` | 1.0 GiB | 4.9 GiB | 20.9% | flat |
| `stackrox/central-db` | 0.9 GiB | 19.9 GiB | 4.3% | |
| `openshift-storage/noobaa-default-backing-store-noobaa-pvc-3aa907b4` | 0.7 GiB | 49.9 GiB | 1.4% | not measured on 11-04 |
| `stackrox/central-db-backup` | 0.3 GiB | 39.9 GiB | 0.8% | flat |
| Other 16 measured PVCs | ~1.9 GiB | ~66 GiB | <35% each | |

Usage for block-mode PVCs (the six 30 Gi OS images and the VM disks) cannot be read from kubelet, so it is **not measured**. Their real consumption is included in the thin pool's 21.74% Data figure.

### Largest reservations relative to use

| PVC(s) | Reserved | Used |
|---|---:|---:|
| Six OS golden images (`rhel8/9/10`, `centos-stream9/10`, `prime-…`), Block | 180 Gi | not measured |
| NooBaa databases ×2 and backing store | 150 Gi | 14.3 GiB |
| Image registry | 100 Gi | 18.9 GiB |
| StackRox `central-db-backup` | 40 Gi | 0.3 GiB |
| TPA `postgres-data` | 45 Gi | 2.8 GiB |

### Orphan candidates (not deleted)

- `trusted-profile-analyzer/importer-8fcc46f77-f4ll2-workdir`, 8 Gi. Its pod `importer-8fcc46f77-f4ll2` has been `Completed` for 12 days. The replacement importer uses `kpch6-workdir`.
- `openshell/workspace-default--grounded-moth`, 2 Gi. No running pod mounts it. Only `openshell-0` is running.
- `mike-devspaces/claim-devworkspace`, 10 Gi. Not mounted because all DevWorkspaces are `Stopped`. This is expected and is not an orphan.

## Evidence and method

- `oc get pv`, `oc get pvc -A`, PVC events, and `oc get dv,vm,dataimportcron`.
- LVMCluster status and spec (`thinPoolConfig`), plus the node annotation `capacity.topolvm.io/vg1`.
- Kubelet `/api/v1/nodes/quark.host.box1.org/proxy/stats/summary`, mapped to PVC claims through the pod specs.
- `oc debug node/quark.host.box1.org` → `lvs` / `vgs` / `lsblk` for thin-pool Data%/Meta% and device sizes. The debug pod was the only object this audit created, and it was removed automatically.

## Change applied: overprovisionRatio 1 → 2

**Applied:** 2026-11-06 23:55 EST, by a live `oc patch` on `LVMCluster/box1-storage` (`openshift-lvm-storage`), path `spec.storage.deviceClasses[0]` (`vg1`) `.thinPoolConfig.overprovisionRatio`. Before patching, a server-side dry run confirmed that the LVMS admission webhook accepts the change in place.

**Management:** the LVMCluster is a manual install with no Argo CD tracking, so nothing reverts the patch. The [cleaned backup](../../manual/backup/operands/lvmcluster.yaml) and the [manual-installs inventory](../../manual/manual-installs-and-secrets.md) now record ratio 2.

**Verification:**

- `vg-manager` reloaded `/etc/topolvm/lvmd.yaml` with `thin-pool.overprovision-ratio: 2` (the container restarted once). LVMCluster stayed `Ready`.
- Node annotation `capacity.topolvm.io/vg1` went from 78.5 GiB to **786.0 GiB** within about 5 seconds.
- `openshift-mta/mta-hub-bucket-volume-claim` (100 Gi) and `mta-hub-database-volume-claim` (10 Gi) became **Bound**, and pod `mta-hub-6fbbf9b7d8-7c4zb` is **Running**.
- The same window also bound four 10 Gi Loki PVCs in `openshift-logging` (ingester storage and WAL, compactor, index gateway).
- Reservations reconcile exactly: 45 PVs totalling 924 GiB, plus three read-only OpenShell VolumeSnapshot LVs (5 GiB), equals 929 GiB. That matches 2 × 857.5 GiB minus the 786 GiB reported capacity.
- Real thin-pool data use did not change: 21.78% after the patch.

**Safety net:** LVMS ships `PrometheusRule` alerts in `openshift-lvm-storage`:

- `ThinPoolDataUsageAtThresholdNearFull` fires at more than 75% data use; `…Critical` fires at more than 85%.
- The matching `ThinPoolMetaDataUsage…` alerts use the same thresholds for metadata.

Whether those alerts route to anyone outside the console is **not verified**.

**Risk:** reservations may now total up to 1,715 GiB on an 857.5 GiB pool. If real writes fill the pool, thin volumes stop accepting writes. Watch the alerts above.

**Rollback:** patch `overprovisionRatio` back to `1`. Volumes that are already bound are not affected. New claims are refused until total reservations fall below the pool size, and they currently exceed it (929 GiB reserved against 857.5 GiB).

**Fedora golden image (not a capacity problem): resolved 2026-11-07 00:18 EST.** `openshift-virtualization-os-images/fedora-3c9d3f5c2fac` had been stuck for 34 hours because its importer pod `importer-prime-f163a15a-…` was rejected with `OutOfpods`. At that time the node was at its 250-pod limit. The limit has since been raised to 400, and 306 pods were active at retry time.

- **Fix:** deleted the stuck pod, and CDI recreated it.
- **Result:** the DataVolume reached `Succeeded`, PVC `fedora-3c9d3f5c2fac` is Bound, and DataSource `fedora` is `Ready=True`. No PVCs remain Pending anywhere in the cluster.
- **Capacity:** the 30 Gi volume was already reserved through the prime PVC, so it adds no new reservation.
- **Observation:** about 350 `Succeeded` pods remain in `box1-ci`. Completed pods were probably a large part of reaching the old 250-pod limit, but this was **not established**.

## Follow-ups and options

These are recommendations only. None has been carried out or tested.

1. **Done:** raised `overprovisionRatio` to 2 (see above).
2. **Trim the OS golden images** to the ones actually used, for example by disabling the RHEL 8, CentOS Stream 9/10, and Fedora DataImportCrons. Each one frees a 30 Gi reservation.
3. **Remove the orphan candidates** (TPA `f4ll2` workdir, OpenShell `grounded-moth` workspace) after confirming with their owners. Together they free 10 Gi.
4. **Watch the growing volumes:** StackRox `scanner-v4-db` (62%) and the active TPA importer workdir (74%).
5. **Right-size oversized PVCs** (registry, NooBaa, TPA Postgres). PVCs cannot shrink, so this requires recreating them and migrating data. Defer unless options 1 and 2 are not enough.

A larger disk is not needed for the current written data (~186 GiB of 857 GiB). It would only be needed if real usage grows or the overprovision ratio must stay at 1.
