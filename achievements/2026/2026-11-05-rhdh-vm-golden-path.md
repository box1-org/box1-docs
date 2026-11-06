# Developer Hub golden path for RHEL 10 image mode VMs

**Date:** 2026-11-05 (America/New_York), about 19:35 to 21:35 EST
**Status:** Complete and verified live through the Developer Hub UI. Tracked in [box1-docs#55](https://github.com/box1-org/box1-docs/issues/55), a sub-issue of [#25](https://github.com/box1-org/box1-docs/issues/25). #55 stays open for its follow-ups. This builds on the [image mode prototype](2026-11-05-rhel-image-mode-poc.md), the [phased onboarding plugin](2026-11-04-rhdh-onboarding-refactor.md) and its [OCI delivery](2026-11-05-rhdh-onboarding-plugin-oci.md).

## Outcome

A developer can now create a RHEL 10 image mode VM from Developer Hub, using the template **Create RHEL 10 Image Mode VM** (`rhel-image-vm`, template version 1.0.0). No manual `oc` is needed. The governance matches the Quarkus golden path:

1. An owned repository is created.
2. An onboarding PR passes the required checks and is merged at its exact head.
3. Argo CD syncs the workload.
4. The first build runs.
5. A promotion PR merges.
6. Verify passes.

After that, every merge to `main` builds and scans a new OS image and records it in box1-workloads-dev as the VM's approved digest. It also moves the `:development` update channel. The guest applies the release deliberately with `sudo bootc upgrade --apply`, and can roll back.

Live result: `vm-golden-check` onboarded in **9 min 06 s** and booted the pipeline-built image. A day-2 release then reached the VM through GitOps, and both upgrade and rollback worked. A Quarkus regression onboarding on the same plugin version behaved exactly as before.

The ERP appliance ([#25](https://github.com/box1-org/box1-docs/issues/25), [#14](https://github.com/box1-org/box1-docs/issues/14)) can now be created from this template. Its data disk, SFTP and TUI target are not part of this work.

## Starting baseline

- **Onboarding plugin 1.1.3:** phase actions accepted only `name` and `sourceRevision`. The bundle check, build (`box1-quarkus-maven`), promote (digest and `replicas` regexes) and verify (`/api/info`, `/q/health`) were Quarkus-specific.
- **`box1-gitops-validate`,** the required check on every box1-workloads-dev PR, applied Deployment, Route and probe rules to every workload, with no opt-out. A single VM workload would have failed every later onboarding PR, Quarkus ones included.
- **The Hub service accounts** could not read VirtualMachines.
- **Argo CD:** checked on the cluster. The application controller could already manage `virtualmachines.kubevirt.io` and `datavolumes.cdi.kubevirt.io` in `managed-by` namespaces, and the `default` AppProject allows everything, so no Argo RBAC change was needed.
- **Storage:** `lvms-vg1` had 11.5 GiB free. The user freed capacity, leaving 96.5 GiB before the live runs.

## Design decisions from spikes

Before writing code, I ran throwaway spikes: an Argo Application `vm-spike` from a temporary box1-docs branch, and the prototype VM. All spike resources were removed afterwards.

- **The disk must not exist before the first build.**
  - A Halted VM whose `dataVolumeTemplates` used a placeholder disk was Healthy. However, when the URL was later changed, the existing DataVolume **kept the placeholder**, because DataVolume specs are immutable.
  - So the onboarding bundle ships a Halted VM with zero digests, plus `datavolume.yaml` generated but **not listed** in the kustomization.
  - The first promotion lists it, pins the disk digest and sets `runStrategy: Always`.
  - A Halted VM that references a DataVolume that does not exist yet is Synced/Healthy in Argo.
- **No Argo `ignoreDifferences` is needed.** After promotion there was no defaulting drift. Later promotions edit only VM metadata annotations, which caused no restart (the VMI UID was unchanged).
- **Admin SSH goes through the guest agent.**
  - KubeVirt `accessCredentials` delivers keys from a Secret through qemu-guest-agent. RHEL allows `guest-ssh-add-authorized-keys`, but the SELinux boolean **`virt_qemu_ga_manage_ssh` is off** by default, and the first attempt failed with `failed to create directory … .ssh: File exists`.
  - The image now sets `setsebool -P virt_qemu_ga_manage_ssh on`.
  - Key edits reach a running VM without a restart. Propagation replaces `authorized_keys`, so the Secret is the single source of keys.
- **Updates are GitOps-promoted (the user's choice).** Each release records `box1.org/os-image-digest` on the VirtualMachine. After the merge and sync, it moves `box1-ci/<name>:development` to exactly that manifest. Applying the update stays a deliberate step in the guest.
- **The template is generic (the user's choice).** ERP specifics come later.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| box1-gitops | [#65](https://github.com/box1-org/box1-gitops/pull/65) | `113149a` | Workload profiles in `box1-gitops-validate`. A `virtual-machine` profile in `box1-gitops-promote` (`plan_updates()`). New Tasks `box1-bootc-build`, `box1-bootc-disk`, `box1-bootc-channel` and `box1-vm-smoke`. Shared SAs moved to `ci/bootc-build.yaml`. Hub and RHDH read access to VMs, VMIs and DataVolumes, and VM kinds in the RHDH Kubernetes tab. Contract tests |
| box1-templates | [#27](https://github.com/box1-org/box1-templates/pull/27) | `8537ec1` | Template `templates/rhel-image-vm` (skeleton and GitOps bundle), registered in the root Location. Plugin 1.2.0 with a `profile` input and the `virtual-machine` implementation. `validate.mjs` coverage and `scripts/test-onboarding-vm.cjs` |
| box1-templates | tag `onboarding-plugin-v1.2.0` | `8537ec1` | Release `box1-onboarding-plugin-release-6fz6w` published `box1-plugins/box1-onboarding-plugin@sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b` |
| box1-gitops | [#66](https://github.com/box1-org/box1-gitops/pull/66) | `2f28d02` | Runtime pin to 1.2.0, opened by the release pipeline |
| box1-gitops | [#67](https://github.com/box1-org/box1-gitops/pull/67) | `c87d904` | PaC check "Details" links go to the OpenShift console (see below) |

**The `service` profile is unchanged.** Plugin records, the `.box1/onboarding.json` marker (no new field), template version `1.1.0`, the commit message and all checks are byte-for-byte as before, so in-flight 1.1.x onboardings resume. The `virtual-machine` profile is recorded in state and in the marker, and every later phase must pass the same profile.

**VM behaviour by component:**

| Component | `virtual-machine` behaviour |
|---|---|
| Bundle check (plugin and `box1-gitops-validate`) | Exactly one VirtualMachine with `os-image-digest` and `source-revision` annotations, and the `serviceca` and `regtoken` update disks. An updater token Secret with no data in Git. Secrets other than the token may hold only SSH public keys. No Deployments, container images or `dataVolumeTemplates`. Unbuilt: Halted, with no DataVolume listed. Promoted: one root DataVolume pinned to `box1-ci/<name>-disk@sha256:…` |
| First build (one PipelineRun as `ci-bootc-release`) | `box1-bootc-build` → `box1-bootc-disk` → `box1-bootc-channel`, returning the image and disk digests. The credential Secret lifecycle is unchanged |
| Release pipeline (in the generated repo) | build → security (observe) → disk → promote (`ci-gitops`) → channel → smoke (`ci-observe`). Channel and smoke run only after a merged promotion |
| Verify | Waits for: VM annotation equals the digest, DataVolume `Succeeded` (a `Failed` import fails at once), VM Ready, `AgentConnected`, and Argo Synced/Healthy |

**Template parameters:**
- `name`, `description`, `owner`, `visibility`;
- one validated SSH public key;
- `cpuCores` 1/2/4, `memory` 2/4/8Gi;
- `rootDiskSize` 12/20/40Gi, defaulting to 12Gi because the OS needs about 11Gi;
- optional `extraPackages`, regex-restricted.

## Validation and evidence

**Offline:**
- box1-gitops: `test-gitops-validate.py` has 14 tests. It renders real kustomize fixtures and re-validates all 5 existing workloads as `service`. `test-gitops-promote.py` has 10.
- box1-templates: `npm run validate` passes; `test:onboarding` 57 of 57 (45 existing plus 12 VM); `test:onboarding-oci` 26 of 26. The PR pipeline `box1-onboarding-plugin-pr-sxkpl` passed.
- **Cross-repo contract:** the rendered template bundle passes #65's VM rules as generated, after `plan_updates()` applies a first promotion, and after a day-2 promotion. The day-2 promotion changed only `virtualmachine.yaml`.
- **Template build:** the rendered skeleton built locally on arm64 with extra packages, and lint stayed at baseline.

**Runtime:** after #66 and a manual `developer-hub` sync, `check-onboarding-runtime.py --live` passed for `sha256:98506a25…`.

**Live onboarding through the Developer Hub UI.** The user started both runs; I verified each phase on the cluster and in the guest.

| Check | Observed |
|---|---|
| Regression `qs-regression-check` (service profile) | `COMPLETE`, with the 1.1.x record shape (`templateVersion` 1.1.0, no profile). `/api/info` served the onboarded `gitRef` |
| `vm-golden-check` onboarding | 20:24:48 → 20:33:54 EST. The repository marker records `profile: virtual-machine` |
| Onboarding PR [box1-workloads-dev#66](https://github.com/box1-org/box1-workloads-dev/pull/66) | Contained exactly the 8 bundle files. `box1-gitops-validate-z2287` passed 5 services under service rules and `vm-golden-check` under VM rules, the first live run of #65 |
| Before the first build | VM Halted, no DataVolume, Argo Synced/Healthy |
| First build `onb-vm-golden-check-c8abaae5` | build 4m 0s → image `a4e23a85…`; disk 2m 26s → `f45a9940…`; channel 4s. The Git credential Secret was cleaned up |
| First promotion [box1-workloads-dev#69](https://github.com/box1-org/box1-workloads-dev/pull/69) | Changed only the disk digest (1 line), the kustomization (+1) and the VM (3 lines) |
| Boot | DataVolume `Succeeded`, VM Ready, `AgentConnected=True`, **`AccessCredentialsSynchronized=True`**, guest RHEL 10.2, Argo Synced/Healthy |
| In the guest | SSH as `cloud-user` with the key from the form worked. `virt_qemu_ga_manage_ssh` on at boot; SELinux Enforcing; no failed units. `vm-golden-check.target` and its services active. **`bootc status` booted `a4e23a85…`, the build's `image-digest`**, tracking `:development` |
| Day-2 release `vm-golden-check-release-ldrcn` (from [vm-golden-check#1](https://github.com/box1-org/vm-golden-check/pull/1)) | All 6 tasks succeeded in 7m59s; image `bf9d1186…`. The promotion [box1-workloads-dev#71](https://github.com/box1-org/box1-workloads-dev/pull/71) changed only `virtualmachine.yaml` (3 lines), and the VMI was not restarted |
| Upgrade, rollback and roll-forward | `bootc upgrade` staged `bf9d1186…` (a 27.6 MB layer delta). After reboot the new login line appeared. `bootc rollback` returned to `a4e23a85…` and the line disappeared. Rolled forward again to the approved digest |
| Negative checks | Anonymous pulls of the image and disk return 401. Rejection of unpinned or started-unbuilt bundles is covered by the tests above; it was not exercised as a live failing PR |

Each test ran once, so the times above are observations, not performance results.

**Check "Details" links.**
- **Cause:** every PaC check linked to `https://dashboard.is.not.configured`, because TektonConfig set the `custom-console-*` settings to `''` and console auto-detection did not fill them. Why auto-detection failed was not established.
- **Fix:** #67 sets them explicitly. The placeholders match PaC's `pkg/consoleui/custom.go`.
- **Result:** after the user synced `pipelines-config` (02:29:50 UTC), new box1-gitops checks link to `…/k8s/ns/box1-ci/tekton.dev~v1~PipelineRun/<run>`. Earlier runs keep the placeholder. That the console pages render was not checked.

## Final operational state

| Item | State |
|---|---|
| Developer Hub | Plugin 1.2.0 (`sha256:98506a25…`), pinned in `box1-gitops/platform/developer-hub/dynamic-plugins.yaml`. `developer-hub` Synced at `2f28d02` or later |
| Template | `rhel-image-vm` 1.0.0, from the box1-templates root Location |
| Platform Tasks and SAs | In `box1-ci`, from `pipelines-ci` (Synced/Healthy) |
| Example VM | `vm-golden-check` in `vm-golden-check-dev`, Argo Application `vm-golden-check` (automated selfHeal). Running `bf9d1186…`, which equals its GitOps `box1.org/os-image-digest`. Kept as the reference instance |
| Build prerequisites outside Git | `box1-ci/redhat-registry-pull` and `box1-ci/etc-pki-entitlement`, documented in `ci/bootc-build.yaml` |

**Cleanup done the same night:**
- **`qs-regression-check`:** decommissioned with the [runbook](../../runbooks/service-decommission.md).
  - GitOps removal [box1-workloads-dev#70](https://github.com/box1-org/box1-workloads-dev/pull/70) (`555f1c3`).
  - Application deleted with its finalizer, which removed the namespace; the PaC Repository finalizer was cleared (0 dependents).
  - Onboarding records, ImageStream and PipelineRun deleted.
  - The repository was deleted by the user and returns 404. Whether its RHDH catalog location was removed first, and the catalog entity 404 checks, were **not verified** in-session (the in-pod catalog call was not authorized).
- **Prototype:** retired, as described in its [log](2026-11-05-rhel-image-mode-poc.md).

## Recovery and follow-ups

- **Plugin rollback:** revert #66, or pin the 1.1.3 digest `sha256:90cba6f1…`, then sync `developer-hub` while no onboarding is running. 1.2.0's `service` path is identical, so rolling back affects only new VM onboardings. A VM onboarding that is already in flight cannot resume on 1.1.3.
- **Platform rollback:** revert #65. Do this only after removing VM workloads from box1-workloads-dev; otherwise the old validator fails every PR.
- **VM rollback:** in the guest, run `sudo bootc rollback --apply`. To rebuild a VM, delete its DataVolume and re-promote. This is **not tested**.
- **Follow-ups** in [#55](https://github.com/box1-org/box1-docs/issues/55):
  - automate refreshing the entitlement copy;
  - move the privileged bootc SAs out of `box1-ci`;
  - optional scheduled `bootc upgrade` and guest reporting of the booted digest (today, approved ≠ applied);
  - identify the ACS policy failing in observe mode;
  - an ERP extension for #25 (data disk, SFTP, TUI target).

**Correction:** comments on #46 and #55 dated "2026-11-06 (America/New_York)" describe work done on the evening of **2026-11-05 EST**; 2026-11-06 was the UTC date.
