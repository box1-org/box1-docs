# D-004 Version number and release

**Decision.** 1.3.0 (next minor; `onboarding-plugin-v1.2.0` already exists and cannot be reused). Changed: `plugins/box1-onboarding/package.json`, README, `scripts/test-onboarding-oci.mjs` PR-body fixture. `oci-package.json` has no version field.

Release is the existing path only: user merges box1-templates#33, pushes tag `onboarding-plugin-v1.3.0` on the merge commit, approves the release PipelineRun, merges the box1-gitops pin PR, then (after checking no active onboarding) syncs `developer-hub`. Rollback digest: `sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b` (1.2.0, revision 8537ec1). Records written by 1.3.0 are readable by 1.2.0 for service and VM (no new keys).

Not done in this run (no authority): merge, tag, release, pin, sync.
