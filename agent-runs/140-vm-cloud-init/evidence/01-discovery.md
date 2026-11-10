# 01 Discovery (2026-11-08, America/New_York)

All read-only. No cluster object was created, changed or deleted.

## Repositories

| Repository | Revision |
| --- | --- |
| box1-templates `main` | `5663eb3` (matches the prompt's baseline) |
| box1-gitops `main` | `4bcc9078ae6d46cd7bdae4c7cec8214221ddcb52` (matches) |
| box1-workloads-dev `main` | `b95b99b2b7aaaeeb2d658a88aa78446cbfc090b0` |
| box1-docs `main` | `3928e84` |
| legacy-erp `main` | `9f51971cf55bbc956841f31bb38adb5c302b3456` |
| vm-golden-check `main` | `21a898e7fac7ff050e377b4c288ad0ea335f1c00` |

`grep -ri 'cloud-init\|cloudinit\|nocloud\|cloudInit'` over box1-templates main: no match.

## Cluster (`oc`, read-only)

- OpenShift `5.0.0-rc.7`, Kubernetes `v1.36.5`.
- CSV `kubevirt-hyperconverged-operator.v5.0.0` Succeeded. `kubevirt` CR `status.operatorVersion: v1.9.0`.
- `oc explain virtualmachine.spec.template.spec.volumes.cloudInitNoCloud` lists `secretRef` (`name`), `networkDataSecretRef`, `userData`, `userDataBase64`, `networkData`, `networkDataBase64`. **`secretRef` is supported**, so the stop condition does not apply.
- VMs: `legacy-erp-dev/legacy-erp` Running, digest `sha256:02b220ebf659211468daff2989b76f7b28750b11a965911f6684619574cf14b3`, volumes `root serviceca regtoken erpdata`. `vm-golden-check-dev/vm-golden-check` Running, digest `sha256:3a0d52cef40fb77e58b56be7df0b99abe4a2ee9659bde0bf622a9f9f328020be`, volumes `root serviceca regtoken`. Neither has a cloud-init volume.
- `vm-golden-check` has `spec.template.spec.domain.firmware.uuid` `cef602ef-…` stored on the VM, equal on the VMI. The legacy name-derived UUID (`CalculateLegacyUUID`: uuid5 of the name in namespace `6a1a24a1-4061-4607-8bf4-a3963d0c5895`, from `pkg/virt-controller/watch/vm/firmware.go`) would be `0cc8f7ad-056f-5126-aa64-003a181838a2`, so this UUID is not name-derived.
- `lvms-vg1` StorageClass, `box1-ci` namespace and `system:image-puller` ClusterRole exist.

## KubeVirt source (`kubevirt/kubevirt` `release-1.9`, read through `gh api`)

- `pkg/cloud-init/cloud-init.go`: NoCloud meta-data `instance-id` = `cloudInitUUIDFromVMI(vmi)` = `vmi.Spec.Domain.Firmware.UUID`. A `secretRef` Secret is read from the key `userdata` or `userData`.
- `pkg/virt-api/webhooks/mutating-webhook/mutators/vm-mutator.go`: on VM create, `setFirmwareDefaultsIfEmpty` sets a random `firmware.uuid` and `serial`.
- Consequence: re-creating a VirtualMachine object gives a new instance-id; restart does not. **Not verified in a guest.**

## cloud-init source (`canonical/cloud-init` tag `24.4`)

- `DataSourceNoCloud.check_instance_id` returns `None` for a disk seed (it reads only seed directories and the kernel command line), so a fresh boot re-reads the cidata disk. With `write_files` at frequency `always`, a rotated Secret applies on VM restart.
- `tools/ds-identify`: a `datasource_list` of one entry plus `None` is used without probing.
- `systemd/disable-sshd-keygen-if-cloud-init-active.conf` stops `sshd-keygen@` when cloud-init is active.
- The default RHEL module lists include `package_update_upgrade_install`, `rh_subscription`, `growpart`, `mounts`, `users_groups`, `set_passwords` and `ssh` (with `ssh_deletekeys: true`), which is why the image pins its own lists.

## Base image (offline)

`registry.redhat.io/rhel10/rhel-bootc@sha256:80485ddb…` was already in local podman storage. Inspected with `podman run --network=none --pull=never`:

- RHEL 10.2; `bootc-1.16.4`, `systemd-257`, `openssh-server-9.9p1`.
- **No `cloud-init` package and no `/etc/cloud`.** `qemu-guest-agent` is not in the base either.
- `90-default.preset` enables `cloud-init-local`, `cloud-init`, `cloud-config` and `cloud-final` services.
- `sshd-keygen@.service` has `ConditionFileNotEmpty=|!/etc/ssh/ssh_host_%i_key`, and `/usr/libexec/openssh/sshd-keygen` deletes existing keys before generating, so the condition must be kept.
- `/usr/lib/sysusers.d` is used (for example `chrony.conf`).

## Not established

- The `cloud-init` version in the RHEL 10 repositories: needs entitlement material, which this run did not handle. The first cloud-init image build records it (test plan step 1).
- Whether the RHEL package ships the sshd-keygen drop-in. The image overrides it either way.
- Whether the installed RHDH `fetch:template` skips paths that render empty. Backstage `templateActionHandler.ts` (`containsSkippedContent`) does on current `master`; RHDH 1.9.7 / Backstage 1.45.3 is recorded in `runbooks/rhdh-onboarding-plugin-oci.md`. The first onboarding with the new template shows it.

## Dependencies

- #131 (Keycloak clients) is OPEN. The live test uses a random placeholder string that authenticates to nothing, which still needs approval to put in a Secret.
- #126 does not name a site service user; this run proposes `box1-site` (D-004).
