# 001 Tracing backend: TempoMonolithic on a PersistentVolume

**Decision:** Red Hat build of Tempo, `TempoMonolithic` named `box1` in `box1-observability`. Backend `pv`, 10 Gi on `lvms-vg1`, 72 h block retention. Stack is `redhat-operators`, channel `stable`, manual InstallPlans.

**Why:**
- User decision 2026-11-06: no new object-storage consumer (#43).
- `TempoStack` requires object storage.
- `memory` storage loses traces on every restart.
- 10 Gi and 72 h are a starting proposal; revise against the measured span rate in Phase 7.

**Tradeoff:** a single replica on an RWO volume, with no HA (single node anyway). Deleting the PVC deletes the traces. No business data is stored.
