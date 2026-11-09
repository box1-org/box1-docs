# D-004 Booted-digest mechanism

**Options considered:**
- **Guest-agent exec.** KubeVirt exposes no general exec. `guestosinfo` reports the OS name and version, not the image digest.
- **Guest heartbeat.** Needs an image change, and the source image does not exist.
- **`virtctl ssh … bootc status --format json`.** This pattern is already proven by `box1-bootc-apply` on `legacy-erp`.

**Chosen:** a new read-only Task, `box1-bootc-status` (box1-gitops#134). It runs as `box1-ci/ci-vm-deploy` and connects with `virtctl ssh` as the guest user `box1-status`.
- The per-instance Role `<instance>-status-reader` allows `get` on the VMI and `get`/`update` on `virtualmachineinstances/portforward`.
- The key is the Secret `box1-ci/vm-instance-status-ssh`.
- The source image must bake the public key with `restrict,command="sudo /usr/bin/bootc status --format json"`. Its sudoers must allow only that command.
- `box1-status` must not be `box1-deploy`, because that user may also run `bootc upgrade --apply`.
- The #140 rule keeps `accessCredentials` for `cloud-user` only, so the guest agent cannot deliver this key.

Verify compares the result with the adopted digest. A mismatch fails verify, and the catalog completion predicate requires the match.

**Interface:** the profile-internal key `bootedDigest(w) -> {digest, pipelineRun}` in `workflow.cjs`. A different mechanism replaces that one function.

**Approval items, not done:**
- the Secret `vm-instance-status-ssh`;
- the `box1-status` user in `site-gateway-os` (#126);
- optionally, a dedicated ServiceAccount instead of `ci-vm-deploy` (review finding 3).

Until the Secret and user exist, verify fails with an explicit message while the VM keeps running. Per the prompt's stop condition, live acceptance is blocked on this approval.
