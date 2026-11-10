# Review pass 1: security and operations (fresh subagent, 2026-11-09)

The reviewer was given the diffs (box1-templates `6d4eef4..ddab663`, box1-gitops `59e1ef0..cd7484d`), the prompt and the contracts. It did not see the implementation reasoning. It ran all local suites (all passed) and its own bypass probes. It made no edits and ran no cluster commands.

| # | Severity | Pass | Finding | Resolution |
| --- | --- | --- | --- | --- |
| 1 | medium | security | A decoy `accessCredentials` block under `spec.template.metadata` hid a real block with `users: [cloud-user, root]` or `noCloud` from `gitops-validate` | **Fixed** in box1-gitops `2030fcb`: exactly one `accessCredentials`/`volumes`/`disks` block, and `noCloud`/`configDrive` refused anywhere. A test was added |
| 2 | medium | security | `gitops-validate` never checked vm-instance RBAC after onboarding; a widened cloud-init observer and a `cluster-admin` ClusterRoleBinding were accepted | **Fixed** in `2030fcb`: Roles and bindings must be exactly the generated set, and ClusterRole/ClusterRoleBinding are refused. Tests were added |
| 3 | medium | security | "Read-only" is a property of the Task, not the credential. `ci-vm-deploy` plus a shared key as `box1-deploy` (which may `bootc upgrade --apply`) would reach every instance | **Mitigated:** a dedicated guest user `box1-status` with a forced-command key and sudo for `bootc status` only, and the key renamed `vm-instance-status-ssh` (templates `69f54c3`, gitops `2030fcb`). **Open:** any box1-ci PipelineRun can still run as `ci-vm-deploy` and mount the key. A dedicated ServiceAccount is a follow-up and needs approval |
| 4 | medium | operations | Verify will fail live until the source image provides the guest user and the key exists | **Recorded** as a stop condition and approval item (D-004, handoff) |
| 5 | low | operations | Disk/OS pairing was trusted from the tag name | **Fixed** in `69f54c3`: the disk's `box1.org/bootc-image` label must equal the approved digest. The Hub gains `get imagestreamimages` in box1-ci (gitops `2030fcb`) |
| 6 | low | security | The requester chooses the token URL host that receives the site credential | **Open:** the host is not restricted. The #140 runbook already asks the operator to check the token URL before assembling the Secret. A host allowlist is a follow-up |
| 7 | low | security | The `PartialObjectMetadata` response is not checked | **Fixed** in `69f54c3`: `Kube.metadata` fails closed. A test was added |
| 8 | low | operations | Resume is keyed by name only; a second requester could resume someone else's instance before the onboarding PR exists | **Open:** follow-up (store a parameter hash in the record). This is the same as the existing profiles |
| 9 | low | operations | No capacity guard beyond the form's enums | **Open:** the capacity note is in `evidence/01-discovery.md`. A ResourceQuota/LimitRange is a follow-up |
| 10 | info | operations | Decommissioning is not in the code PRs | **Done** in this box1-docs PR (`runbooks/service-decommission.md`) |
| 11 | info | security | TOFU host keys; virtctl downloaded without a checksum (same as `bootc-apply`); the Hub's existing broad box1-ci Secret rights | **Recorded**, unchanged |

After the repairs: `test:onboarding` 106/106, `validate` PASS, `test-gitops-validate` 95 OK. The cross-check still validates both instances, unbuilt and promoted.
