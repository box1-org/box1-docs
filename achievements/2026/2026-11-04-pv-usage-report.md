# Box1 PV usage report — 2026-11-04

**Snapshot time:** 2026-11-04, America/New_York (live OpenShift query during this chat)

## Outcome

Box1 currently has **25 Bound persistent volumes** on storage class `lvms-vg1`, with **829 GiB requested capacity** in total. One OpenShift node was reported (`quark.host.box1.org`).

Kubelet volume statistics were available for **16 mounted filesystem PVCs**: **87.7 GiB used of 532.0 GiB reported filesystem capacity (16.5%)**. The aggregate is a usage snapshot for mounted filesystems, not backend thin-pool consumption.

## PV inventory

| Scope | Count | Requested capacity |
|---|---:|---:|
| Bound PVs, all modes | 25 | 829 GiB |
| Filesystem PVs | 20 | 679 GiB |
| Block PVs (OpenShift Virtualization images) | 5 | 150 GiB |

All listed PVs were `Bound`, used `lvms-vg1`, and had reclaim policy `Delete` at collection time. No `Released` or `Failed` PV was observed.

## Measured mounted PVCs

| Namespace / PVC | Used | Reported capacity | Use |
|---|---:|---:|---:|
| `vllm/vllm-model-cache` | 43.4 GiB | 149.9 GiB | 29.0% |
| `stackrox/scanner-v4-db` | 22.6 GiB | 39.9 GiB | 56.5% |
| `openshift-storage/noobaa-db-pg-cluster-1` | 6.8 GiB | 49.9 GiB | 13.7% |
| `openshift-storage/noobaa-db-pg-cluster-2` | 6.8 GiB | 49.9 GiB | 13.6% |
| `rhdh/dynamic-plugins-root` | 1.0 GiB | 4.9 GiB | 20.5% |
| `openshift-image-registry/image-registry-storage` | 4.5 GiB | 99.9 GiB | 4.5% |
| `stackrox/central-db` | 0.6 GiB | 19.9 GiB | 3.2% |
| `stackrox/central-db-backup` | 0.3 GiB | 39.9 GiB | 0.8% |
| Other 8 measured PVCs | 1.8 GiB | 77.8 GiB | 2.3% |

The largest measured consumers were `vllm-model-cache` and `stackrox/scanner-v4-db`.

## Not measured

The five 30-GiB virtualization image PVCs are `volumeMode: Block`; their block-level data usage was not exposed by the kubelet volume summary and is therefore marked **not measured**. Four filesystem PVCs were Bound but had no matching mounted volume entry in the node summary at collection time: the two Trusted Profile Analyzer importer workdirs, `openshell/workspace-default--grounded-moth`, and the NooBaa backing-store PVC. Their usage is also **not measured**.

## Evidence and method

Collected with `oc get pv -o wide`, `oc get pvc -A`, and the node proxy endpoint `/api/v1/nodes/quark.host.box1.org/proxy/stats/summary`. PVC usage was mapped from kubelet pod volume statistics to pod specs and PVC claims. The report does not infer storage-array or LVM thin-pool consumption from PVC requested capacity.

## Follow-up

For capacity planning, collect the LVM/ODF backend pool metrics separately and inspect the five block-mode image PVCs from their consuming virtual machines or storage backend. Re-run this snapshot after workload changes; this report is point-in-time evidence.
