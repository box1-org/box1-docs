# Box1 CPU request right-sizing — 2026-11-09

**Window:** 2026-11-09, 08:29–09:12 EST (America/New_York)
**Related:** [OpenShift AI removal](2026-11-09-openshift-ai-removal.md) (same morning, separate log) · [PV capacity audit](2026-11-06-pv-capacity-audit.md) (the storage-side counterpart of this audit)

## Outcome

Box1's single node went from **91.3% to 67.0% of allocatable CPU requested**, freeing **7,648m**. CPU available to schedule grew from **2,733m to 10,381m**. Before the change, any new pod larger than about 2.7 cores would have stayed Pending, even though the node was using only about 27% of its CPU.

| Change | Mechanism | Freed | Status |
| --- | --- | ---: | --- |
| ODF/NooBaa requests lowered | Live `oc patch` of `StorageCluster/ocs-storagecluster` | ~2,450m | **Mitigation.** Applied and verified, but not in Git. Tracked in [box1-docs#152](https://github.com/box1-org/box1-docs/issues/152) |
| Lightspeed requests lowered | `OLSConfig` override in [box1-gitops#137](https://github.com/box1-org/box1-gitops/pull/137) | 2,200m | **Complete.** GitOps-managed |
| OpenShift AI removed | Uninstall, plus [box1-gitops#138](https://github.com/box1-org/box1-gitops/pull/138) | 3,200m | **Complete.** See the [removal log](2026-11-09-openshift-ai-removal.md) |

A snapshot dashboard of the requests, with the progress since the first scan, is published as a private Claude artifact: [Box1 CPU Requests](https://claude.ai/artifact/9rAnWivzueDqMuuA4MPESM). It is visible only to its owner unless shared, and it does not refresh on its own.

## Starting baseline (08:29 EST)

The cluster is a single node, `quark.host.box1.org`: control plane and worker, 32 cores, **31,500m allocatable**.

| Measure | Value |
| --- | ---: |
| Requested by 317 scheduled pods (53 with no CPU request) | **28,767m (91.3%)** |
| Available to schedule | **2,733m** |
| Container limits | 110,778m (351%, overcommitted) |
| Node CPU in use (one `oc adm top` sample) | 8,666m (27%) |

**Method.** Each pod's effective request was computed from its spec: the larger of (containers plus sidecar init containers) and (largest init container plus sidecars), plus pod overhead. Completed and failed pods were excluded. The total matched the Allocated resources line of `oc describe node` exactly.

**Largest namespaces by request:**
- `openshift-storage`: 4,123m requested, 192m used
- `openshift-lightspeed`: 2,820m requested, 16m used
- `openshift-gitops`: 1,875m requested, 753m used
- `trusted-profile-analyzer`: 1,760m requested, 25m used
- `openshift-ingress`: 1,725m requested, 15m used
- `stackrox`: 1,651m requested, 1,473m used
- `redhat-ods-operator`: 1,500m requested, 19m used

Seventeen pods each requested at least 500m while using less than 10% of it. Together they held 11,524m of reserved but unused CPU.

## What changed

Each new request was sized from Prometheus data in `openshift-monitoring`: `rate(container_cpu_usage_seconds_total[5m])`, taking the per-container maximum over a 7-day window. The `lightspeed-rhokp` pod had only been running since 2026-11-07, so its sample covers about 2.3 days. Memory requests were not changed.

| Component | Request before → after | CPU limit | 7-day p95 / max |
| --- | --- | --- | --- |
| `noobaa-core-0` (`core`) | 999m → **250m** | 999m (unchanged) | 125m / 151m |
| `noobaa-endpoint` | 999m → **100m** | 999m (unchanged) | 4m / 8m |
| `noobaa-db-pg-cluster-1`, `-2` | 500m → **100m** each | 500m (unchanged) | 31m / 43m |
| `lightspeed-rhokp` | 2 CPU → **200m** | none | 55m / 64m |
| `lightspeed-app-server` / `lightspeed-service-api` | 500m → **100m** | none | 2m / 96m |

**ODF/NooBaa (applied about 08:45 EST).**
- Change: `oc patch storagecluster ocs-storagecluster -n openshift-storage --type merge` setting `spec.resources` keys `noobaa-core`, `noobaa-endpoint` and `noobaa-db`.
- Propagation: `ocs-operator` copied the values to `NooBaa/noobaa` (`coreResources`, `endpoints.resources`) and to the CNPG `Cluster/noobaa-db-pg-cluster`.
- Ownership: this StorageCluster is not tracked by Argo CD or stored in `box1-gitops`. The exact patch and its rollback are recorded in [box1-docs#152](https://github.com/box1-org/box1-docs/issues/152).
- Saved baselines: the pre-change StorageCluster, NooBaa and CNPG manifests were saved locally on the workstation only, not in this repository.

**Lightspeed.**
- Change: [box1-gitops#137](https://github.com/box1-org/box1-gitops/pull/137), squash-merged as `7a1da45` at 08:49 EST. It sets `spec.ols.deployment.rhokp.resources` and `spec.ols.deployment.api.resources` in `platform/lightspeed/config/olsconfig.yaml`.
- Why memory and storage are restated: setting `resources` replaces the operator's default block, so the memory requests (2Gi and 1Gi) and the rhokp `ephemeral-storage: 75Gi` request are restated unchanged.
- Documentation: the Lightspeed README gained a "CPU requests" section.
- Sync: the `lightspeed` Application syncs manually. It was synced at 08:50:19 EST.

**Tradeoffs.**
- Requests now sit well below the operator defaults. Running this far below the defaults is **not established** as vendor-supported, which is acceptable for this lab.
- CPU limits were left in place, or absent, so every component can still burst to its previous ceiling.
- The NooBaa endpoint autoscaler (`noobaa-hpav2`, 1–2 replicas) targets 80% of the request. Sustained S3 load above about 80m now adds the second replica.

## Validation and evidence

| Time (EST) | Milestone | Node CPU requested | Evidence |
| --- | --- | ---: | --- |
| 08:29 | First scan | 28,767m | Full snapshot of all pods |
| 08:48 | ODF/NooBaa lowered | 26,519m | `oc describe node` total only. It also reflects unrelated pods starting and stopping, so it under-states the ~2,450m ODF change |
| 08:52 | Lightspeed lowered | 24,319m | Full snapshot of all pods |
| 09:06 | OpenShift AI removed | **21,119m** | Full snapshot of all pods |

Net change by namespace, 08:29 → 09:06:

| Namespace | Before → after | Change |
| --- | --- | ---: |
| `openshift-storage` | 4,123m → 1,675m | −2,448m |
| `openshift-lightspeed` | 2,820m → 620m | −2,200m |
| `openshift-ingress` | 1,725m → 125m | −1,600m |
| `redhat-ods-operator` | 1,500m → 0m | −1,500m |
| `redhat-ods-applications` | 100m → 0m | −100m |
| `openshift-terminal` | 0m → 200m | +200m (a web terminal session started; unrelated) |

**ODF/NooBaa.**
- Pods: within about 20 seconds, `noobaa-core-0`, both database instances and a new `noobaa-endpoint` pod were Running and Ready with the new requests. None has restarted since.
- Status: the CNPG cluster reported "Cluster in healthy state", and `NooBaa/noobaa` and the StorageCluster stayed `Ready`.
- Logs: NooBaa errors were limited to start-up connection-refused messages until 08:45:53 EST.
- Loki reads: Loki's object-store `iter` operations succeeded after the restart.
- Loki writes: `logging-loki-ingester-0` uploaded successfully at 09:01:19 EST. There were zero Loki object-store failures between 08:42 and 09:12 EST.
- **Not tested:** a direct put/get/delete through an ObjectBucketClaim. That probe needs the OBC's access keys, and this session's permissions blocked reading them.

**Lightspeed.**
- Pods: new `lightspeed-rhokp` and `lightspeed-app-server` pods rolled out with the new requests and became Ready. rhokp was Ready by 08:51:34 EST, within 75 seconds of the sync.
- Status: every `OLSConfig` component condition was True. The alerts adapter is the exception; it is disabled by design. `overallStatus` was `Ready`.
- Logs: the API logged "LLM connection checked - LLM is ready".
- **Not tested:** a chat through the console assistant.

**Cluster-wide checks after all three changes.**
- All cluster operators were Available and not Degraded.
- Every Argo CD Application was Synced/Healthy.
- No pods newly entered a non-running state.

## Final operational state

| Item | State | Managed by |
| --- | --- | --- |
| Node CPU requested | 21,119m of 31,500m (67.0%), 10,381m available | — |
| Lightspeed requests (200m / 100m) | Live and matching `box1-gitops` `main` | Argo CD `lightspeed` (manual sync) |
| NooBaa requests (250m / 100m / 100m ×2) | Live only | **Manual override** on `StorageCluster/ocs-storagecluster`, not in Git |
| OpenShift AI | Removed | See the [removal log](2026-11-09-openshift-ai-removal.md) |

Upgrade caveats:
- **NooBaa:** the override lives in `StorageCluster.spec.resources`, and ODF upgrades preserve that field. Recreating the StorageCluster or reinstalling ODF would return the `resourceProfile: balanced` defaults.
- **Lightspeed:** a Lightspeed operator upgrade that renames `spec.ols.deployment.*` would surface as an Argo CD diff on the `lightspeed` Application.

## Recovery and follow-ups

- **Revert NooBaa:** `oc patch storagecluster ocs-storagecluster -n openshift-storage --type json -p '[{"op":"remove","path":"/spec/resources"}]'`. This restores the profile defaults and restarts the same pods, with a brief S3 interruption for Loki and RHTPA. Not exercised.
- **Revert Lightspeed:** remove the `deployment` block from `platform/lightspeed/config/olsconfig.yaml` through a PR, then sync `lightspeed`. Not exercised.
- **Open in [box1-docs#152](https://github.com/box1-org/box1-docs/issues/152):**
  - Decide GitOps ownership for the StorageCluster and record the override in `box1-gitops`.
  - Run a direct OBC put/get/delete.
  - Recheck NooBaa CPU use and endpoint HPA scaling after a week.
- **Not tracked in the backlog: remaining idle requests.** Six pods each request at least 500m and use under 10% of it, 4,053m of idle reservation in total:
  - StackRox `scanner-v4-matcher`: 1,000m
  - TPA `importer`: 1,000m
  - TPA `server`: 500m
  - Developer Hub: 600m
  - Logging collector `box1`: 500m
  - MTA hub: 500m
- **Not tracked in the backlog: pods using far more than they request.** `kube-apiserver` used about 4,029m against a 290m request, and `openshift-gitops-application-controller-0` about 743m against 250m. The scheduler does not see that load.
- **Not tracked in the backlog: single samples.** The "used now" figures are one sample per scan, not peaks.
