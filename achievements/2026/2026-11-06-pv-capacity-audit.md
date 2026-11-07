# Box1 PV capacity audit — 2026-11-06

**Snapshot time:** evening of 2026-11-06, America/New_York (live OpenShift and LVM queries during this chat)
**Previous snapshot:** [2026-11-04 PV usage report](2026-11-04-pv-usage-report.md)

## Outcome

The LVMS thin pool is **about 22% written but 91% reserved**. Box1's storage problem is the allocation policy (`overprovisionRatio: 1`), not a full disk. Under that ratio every PVC reserves its full requested size at bind time. Only **78.5 GiB** is left to reserve, so new large claims are refused even though roughly 670 GiB of the pool has never been written.

Visible impact: the MTA hub cannot start. `openshift-mta/mta-hub-bucket-volume-claim` (100 Gi) is Pending with `NotEnoughCapacity`, and `mta-hub-database-volume-claim` (10 Gi) is waiting on the same unscheduled pod.

This was a read-only audit. Nothing was changed, resized, or deleted.

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

## Follow-ups and options

These are recommendations only. None has been carried out or tested.

1. **Raise `overprovisionRatio`** on device class `vg1`, for example to 2. This is the largest lever: it unblocks MTA and future claims without adding hardware. The trade-off is that real thin-pool exhaustion becomes possible, so pair the change with alerting on thin-pool Data% and Meta%. Whether LVMS accepts an in-place change to this field is **not verified**. Back up the LVMCluster spec (`manual/backup/operators/lvm-storage.yaml`) before trying.
2. **Trim the OS golden images** to the ones actually used, for example by disabling the RHEL 8, CentOS Stream 9/10, and Fedora DataImportCrons. Each one frees a 30 Gi reservation.
3. **Remove the orphan candidates** (TPA `f4ll2` workdir, OpenShell `grounded-moth` workspace) after confirming with their owners. Together they free 10 Gi.
4. **Watch the growing volumes:** StackRox `scanner-v4-db` (62%) and the active TPA importer workdir (74%).
5. **Right-size oversized PVCs** (registry, NooBaa, TPA Postgres). PVCs cannot shrink, so this requires recreating them and migrating data. Defer unless options 1 and 2 are not enough.

A larger disk is not needed for the current written data (~186 GiB of 857 GiB). It would only be needed if real usage grows or the overprovision ratio must stay at 1.
