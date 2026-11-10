# D-002 Which disk an instance imports

**Finding (observed 2026-11-09):** the source's DataVolume points at its *first* release disk, and DataVolume specs are never changed. On `vm-golden-check`:

| Item | Revision | Digest |
| --- | --- | --- |
| Git DataVolume | `c8abaae` (first release) | `sha256:f45a99…` |
| Approved revision | `21a898e` | OS `sha256:3a0d52…` |
| `box1-ci/vm-golden-check-disk:21a898e…` | `21a898e` | `sha256:6fa3fe…` |

Adopting the Git DataVolume digest would boot an older OS than the approved digest.

**Decision:** the instance imports `box1-ci/<source>-disk:<approved revision>`. This is the disk that the source's release pipeline built from the approved image. Before using it, `resolve-source` checks two things:
- `box1-ci/<source>:<revision>` is the approved OS digest;
- the disk's `box1.org/bootc-image` label names `box1-ci/<source>@<approved digest>`.

It reads that label through `imagestreamimages`; box1-gitops#134 adds the Hub permission. The Git DataVolume digest is recorded only for reference (`firstReleaseDiskDigest`).

**Deviation:** the task brief said to adopt "the DataVolume disk digest" from Git. That would be wrong after any day-2 release of the source, so this run did not do it.
