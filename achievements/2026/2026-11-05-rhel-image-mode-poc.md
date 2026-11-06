# RHEL 10 image mode VM prototype: build, boot, update and roll back

**Date:** 2026-11-05 (America/New_York), about 17:20 to 19:35 EST
**Status:** Complete and retired. Tracked in [box1-docs#46](https://github.com/box1-org/box1-docs/issues/46) (closed), a sub-issue of [#25](https://github.com/box1-org/box1-docs/issues/25). The prototype became the Developer Hub golden path in the [RHEL image mode VM golden path log](2026-11-05-rhdh-vm-golden-path.md). Its repository, [box1-org/rhel-image-poc](https://github.com/box1-org/rhel-image-poc), is archived.

## Outcome

A RHEL 10 image mode (bootc) operating system built from a Git repository now boots both locally and on OpenShift Virtualization, and updates in place:

- **Local:** an arm64 VM on an Apple Silicon Mac, under vfkit.
- **OpenShift Virtualization:** an x86_64 VM.
- **Build:** a Pipelines-as-Code release builds the OS image, runs the TPA and ACS scans, and produces a KubeVirt disk.
- **Updates:** the VM changed OS image in place with `bootc switch`, `bootc upgrade` and `bootc rollback` from the in-cluster registry. `qemu-guest-agent` connected to KubeVirt.

The prototype settled the questions a golden path needed answered: base image, entitlement, build privilege, disk creation, registry trust, and update mechanics. It deliberately cut corners on delivery (see "Temporary deviations"). Those were removed by the golden path and the prototype was retired on the same day.

## Starting baseline

- **Cluster:** single-node OpenShift on x86_64 (`quark`, RHCOS 10.2). OpenShift Virtualization was installed, with a `rhel10` DataSource and one unrelated `vm-sandbox` VM. HyperConverged reported `Available=False` only because of the MigController condition; VMs ran normally. OpenShift Pipelines 1.24.3.
- **Workstation:** Apple Silicon (arm64) with podman 6.1.3. Its machine was rootless (applehv). It had no `registry.redhat.io` login, and no `virtctl` or `qemu`.
- **Repositories:** no bootc, KubeVirt or VM content existed. The onboarding plugin and the required `box1-gitops-validate` check accepted only Quarkus-style Deployment workloads.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| CI identities | [box1-gitops#58](https://github.com/box1-org/box1-gitops/pull/58) | `e522445` | PaC Repository, `ci-bootc-check` and `ci-bootc-release` (privileged), image-puller for the VM namespace |
| Report links | [box1-gitops#59](https://github.com/box1-org/box1-gitops/pull/59), [#60](https://github.com/box1-org/box1-gitops/pull/60) | `4375a07`, `b8054eb` | `box1-security-gates` returns `rhacs-url` and `rhtpa-sbom-url` (see below) |
| Prototype repo | [rhel-image-poc#1](https://github.com/box1-org/rhel-image-poc/pull/1)–[#8](https://github.com/box1-org/rhel-image-poc/pull/8) | `0f38723` … `f399ed7` | Containerfile, PR and release pipelines, guest agent, entitled builds, update channel, docs. #3 was closed, superseded by #7 |

**Base and contents.**
- **Base image:** `registry.redhat.io/rhel10/rhel-bootc:10.2`, pinned by index digest `sha256:80485ddb…`. The same Containerfile builds arm64 and amd64.
- **Already in the base:** python3 3.12, sshd, sudo, podman 5.8 and bootc 1.16.
- **Not in the base:** cloud-init and qemu-guest-agent. So KubeVirt cloud-init user data does nothing on this image.

**Decisions with consequences:**

- **Privileged builds.** The base has 66 layers. Unprivileged buildah with vfs storage would copy the full filesystem once per layer, roughly 100 GB per build, so the image build needs overlay storage and therefore a privileged pod. bootc-image-builder needs one too. Two dedicated SAs carry the `privileged` SCC. Any PipelineRun in `box1-ci` could name them, which is recorded as a follow-up.
- **Entitlement as a build secret.** Installing packages uses the cluster's Simple Content Access certificate, `openshift-config-managed/etc-pki-entitlement`. It is copied, with the user's approval, to `box1-ci/etc-pki-entitlement` and passed only as buildah `--secret` mounts. A text scan of the built image found no keys or certificates. Repository definitions are in `build/repos/rhel10-cdn.repo`, which holds no credentials.
- **Registry credentials outside Git.** `box1-ci/redhat-registry-pull` holds only the `registry.redhat.io` entry from the cluster pull secret.
- **Pipeline changes land first.** The PaC Repository uses `pipelinerun_provenance: default_branch`, so a PR's checks run the pipeline definitions from `main`. A pipeline change must merge before the Containerfile change that depends on it. Rhel-image-poc#6 had to be split out of #5 for this reason.
- **Update channel.** Installed systems track `image-registry.openshift-image-registry.svc:5000/box1-ci/<name>:<channel>`. The release moves the channel tag by copying the manifest bytes, so `bootc status` digests equal the pipeline's `image-digest`.
- **Registry trust and credentials in the guest at runtime.** KubeVirt attaches two disks: the namespace's auto-rotated `openshift-service-ca.crt` ConfigMap, and a pull token for a dedicated SA. A boot-time unit installs the CA under `/etc/containers/certs.d/` and writes `/run/ostree/auth.json` (tmpfs, 0600). Nothing is baked into the image.
- **No unattended reboots.** `bootc-fetch-apply-updates.timer` is disabled, and updates are applied with `bootc upgrade --apply`.

## Validation and evidence

Detailed evidence is in the [#46 comments](https://github.com/box1-org/box1-docs/issues/46).

| Test | Expected | Observed |
|---|---|---|
| Local arm64 build and boot | Lint passes; target, service and bootc status are correct | Lint: 12 passed and 1 warning, from a file the base image ships. VM booted under vfkit 0.6.4; `box1-poc.target`, heartbeat active, SELinux Enforcing, `bootc status` arm64 10.2 |
| PR pipeline on the cluster | Build and lint, no push | `rhel-image-poc-pr-bpp6h` succeeded under the `privileged` SCC |
| First release `rhel-image-poc-release-ppww5` | Image, scans and disk | Build 3m41s, disk 2m31s; image `68a70af4…`, 1013 MB qcow2. TPA SBOM accepted, ACS scan exit 0, ACS policy check **fail** (report-only, observe mode) |
| VM on OpenShift Virtualization | Boots the pipeline image | DataVolume `Succeeded`, VM Running. `bootc status` booted `68a70af4…`, equal to `image-digest`; ttyS0 serial getty active |
| Anonymous registry pull | Denied | HTTP 401 |
| Entitled build (`qznnx`) | Guest agent installed on x86_64 | `qemu-guest-agent-10.1.0-16.el10_2.5` installed, lint at baseline |
| `bootc switch` to `:main` | Moves off the temporary local tag | Pulled 1 new layer (19.3 MB) of 67. Booted `d30353de…`, `AgentConnected=True` |
| `bootc upgrade` and `bootc rollback` | Both directions work | Upgraded to `d8430261…` (release `shcrc`), then rolled back to `d30353de…`. No failed units |

**Report links.** Release runs now link to the scanned image in ACS and to the SBOM in TPA.
- The first ACS link, from #59, used the image digest, which ACS does not accept. The ACS console addresses images by a UUIDv5 of the image's full name and digest (`NewImageV2ID` in StackRox).
- #60 resolves the ID through Central's API, deriving it when needed, and adds the TPA `/sboms/<id>` link.
- The derivation reproduced the user's working URL exactly. I have not opened either page in a browser.

**Tests not performed:** an interactive `virtctl console` session (the getty and kernel arguments were checked instead), and whether ACS shows images that were scanned but never deployed.

## Temporary deviations (all removed the same day)

| Deviation | How it was resolved |
|---|---|
| VM, DataVolume and namespace applied with `oc apply` | Golden-path VMs are Argo-managed through box1-workloads-dev |
| Inline `taskSpec`s in the repo | Central `box1-bootc-*` Tasks in box1-gitops ([#65](https://github.com/box1-org/box1-gitops/pull/65)) |
| Disk digest edited by hand, no promote task | Plugin first promotion, plus `box1-gitops-promote` with `workload-profile: virtual-machine` |
| Admin SSH key baked into the disk | KubeVirt `accessCredentials` through qemu-guest-agent |
| Onboarding plugin bypassed | Plugin 1.2.0 `virtual-machine` profile |

`redhat-registry-pull` and `etc-pki-entitlement` remain on purpose. They are shared build prerequisites, created outside Git and documented in `box1-gitops/platform/pipelines/ci/bootc-build.yaml`.

## Final operational state

Retired on 2026-11-05:
- **Namespace:** `rhel-image-poc` deleted, including its VM and 20Gi `lvms-vg1` disk; no PV remains.
- **Build leftovers in `box1-ci`:** ImageStreams `rhel-image-poc` and `rhel-image-poc-disk`, ConfigMap `rhel-image-poc-admin-key` and the POC PipelineRuns deleted.
- **CI entries:** the PaC Repository and image-puller binding were removed by [box1-gitops#68](https://github.com/box1-org/box1-gitops/pull/68) (`2b97398`).
  - The prune left the Repository on `foregroundDeletion`, as the [decommission runbook](../../runbooks/service-decommission.md) describes.
  - It had no dependents, so its finalizer was cleared. `pipelines-ci` is Synced/Healthy.
- **Repository:** `box1-org/rhel-image-poc` is archived, and the history is kept.
- **Workstation:** the local VM disk and test images were removed.

The `ci-bootc-*` SAs and their bindings were kept, and now live in `ci/bootc-build.yaml` for the golden path.

## Recovery and follow-ups

- **Restoring the prototype:** unarchive the repository, restore `platform/pipelines/ci/rhel-image-poc.yaml` from `2b97398^`, and re-run its release. The cluster objects were not backed up; they are reproducible from the repository.
- **Follow-ups** are tracked in [box1-docs#55](https://github.com/box1-org/box1-docs/issues/55):
  - automate refreshing the `etc-pki-entitlement` copy, which the Insights operator rotates;
  - move the privileged bootc SAs out of the shared `box1-ci` namespace;
  - identify the ACS policy that fails the observe-mode check.

**Correction:** progress comments on #46, and early comments on #55, are dated "2026-11-06 (America/New_York)". The work happened on the evening of **2026-11-05 EST**; 2026-11-06 was the UTC date.
