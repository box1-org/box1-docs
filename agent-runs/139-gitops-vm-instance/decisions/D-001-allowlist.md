# D-001 vm-instance source allowlist: location and format

**Decision (2026-11-08, agent run, reviewable in box1-gitops#132):** the allowlist is the Python tuple `VM_INSTANCE_SOURCES` near the top of the `box1-gitops-validate` script in `box1-gitops/platform/pipelines/tasks/gitops-validate.yaml`.
- Each entry is a bare `box1-org` repository name matching `[a-z][a-z0-9-]{2,39}`.
- The disk image is `box1-ci/<entry>-disk`.
- The initial value is `('site-gateway-os',)`, the first source decided on #126 and #137.

**Why not a ConfigMap:**
- The Task would need a volume, and the tests would need a second input.
- The allowlist could drift from the validator version.
- A tuple in the Task is reviewed in the same box1-gitops PR as the rules, and is versioned with them.

**To add a source:** open a box1-gitops PR that edits the tuple, then sync `pipelines-ci`.

**Consequence:** #138 must add any new source here before an instance of it can pass validation.
