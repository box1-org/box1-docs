# D-006 Day-2 vm-instance promotion does not swap the DataVolume digest — OWNER DECISION NEEDED

**Prompt and owner decision:** "a day-2 instance promotion also swaps the DataVolume digest, because there is no channel to follow". The #139 comment says each instance's promotion updates its own DataVolume digest.

**Implemented:** day 2 changes only `virtualmachine.yaml` annotations (`os-image-digest`, `source-revision`, `build-pipelinerun`), as for `virtual-machine`. The first promotion still writes the DataVolume digest.

**Evidence for the deviation** (read-only, 2026-11-08):
- CDI 5.0.0 registers the webhook `cdi-api-datavolume-validate` for `CREATE` and `UPDATE` on `datavolumes`.
- The existing promote code states "The DataVolume spec is immutable, so it is only ever written here".
- Both instance DataVolumes on the cluster (`legacy-erp-root`, `vm-golden-check-root`) are retained and `Succeeded`, not garbage-collected.
- Upstream CDI rejects DataVolume spec changes on update. This is from knowledge of the upstream source and was **not tested** here, because testing needs a mutation (even a server dry-run was out of this run's authority).

**Effect if the swap were implemented:**
- the promotion PR merges, then the Argo sync fails on admission and the release fails;
- even if it applied, the existing PVC would not be re-imaged.

**Owner options:**
1. Accept: the `box1.org/os-image-digest` annotation is the per-instance record, and the DataVolume records the image the root disk was first imported from. In-guest upgrade to the pinned digest is #141.
2. Overrule: implement the swap together with a re-image mechanism, for example a new DataVolume name per digest plus a VM volume switch. That is a disk-replacing design for #141.
