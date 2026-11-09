# Live test plan: box1-docs#140 cloud-init (NoCloud)

**Status: not run.** Each step below needs the owner's approval, because it creates a repository, Secrets, a namespace or VMs, or deletes VMs and disks. The unattended run that wrote this plan was not authorized to change the cluster. Run it after the `box1-templates` PR that adds `cloudInit` is merged and Developer Hub has refreshed the template.

Record redacted output for each step in `../evidence/` (for example `evidence/10-live-boot.md`). Never record the content of `/etc/box1/credentials/*` or the Secret's data.

Capacity: this plan adds three VMs (one 2 vCPU/4 GiB, two 1 vCPU/2 GiB) and about 37 GiB on `lvms-vg1` (three 12 GiB root disks and a 1 GiB data disk). Check LVMS headroom first, as in the [2026-11-06 PV capacity audit](../../../achievements/2026/2026-11-06-pv-capacity-audit.md).

## 1. Build a cloud-init test image (approval: Golden Path onboarding)

Create `cloudinit-check` from Developer Hub with **Create RHEL 10 Image Mode VM**, with **Per-instance identity with cloud-init** checked and all other values at their defaults. This builds `box1-ci/cloudinit-check` and `box1-ci/cloudinit-check-disk`, and boots VM `cloudinit-check` **without** a NoCloud disk.

The build itself answers three discovery questions that need entitlement access: the `cloud-init` version in the RHEL 10 repositories, the systemd unit names, and whether `bootc container lint` accepts the image. Record them from the build log:

```sh
oc -n box1-ci get pipelinerun -l pipelinesascode.tekton.dev/repository=cloudinit-check
tkn -n box1-ci pipelinerun logs <release-run> -t build | grep -E 'cloud-init-[0-9]|Created symlink|is-enabled|lint'
```

Then, on the VM without a NoCloud disk (scenarios: *boot without NoCloud disk*, *guest agent SSH unaffected*, *registry-setup still works*):

```sh
virtctl ssh -n cloudinit-check-dev cloud-user@vm/cloudinit-check -c '
  systemctl is-system-running; rpm -q cloud-init
  sudo cloud-init status --long              # expect done (or "degraded done" for the None fallback), DataSourceNone
  sudo cloud-init schema --system            # expect valid
  ls /etc/box1 2>&1                          # expect: No such file or directory
  ls /etc/ssh/ssh_host_*_key.pub             # host keys exist (made by sshd-keygen, not cloud-init)
  systemctl status sshd-keygen@ed25519 --no-pager | head -5
  sudo ls -la /root/.ssh 2>&1                # expect no cloud-init changes
  systemctl is-active sshd qemu-guest-agent box1-registry-setup
  sudo ls -l /run/ostree/auth.json /etc/pki/ca-trust/source/anchors/
  sudo bootc upgrade --check
  getent passwd box1-site; id cloud-user; sudo ls /etc/sudoers.d/
  sudo grep -rh PasswordAuthentication /etc/ssh/sshd_config.d/ || true
  systemd-analyze blame | grep -i cloud | head'
```

Expected: the system is `running` with no failed units, host keys exist although cloud-init is active, cloud-init reports `DataSourceNone` and changed nothing, SSH through the guest agent works, `cloud-user` is unchanged (no `90-cloud-init-users` sudoers file), and the registry token and CA are installed. Record `DISK_DIGEST` from `oc -n cloudinit-check-dev get vm cloudinit-check -o jsonpath='{.metadata.annotations.box1\.org/os-image-digest}'` and the matching `cloudinit-check-disk` digest from the DataVolume URL.

## 2. Two identities from one digest (approval: namespace, box1-ci RoleBinding, Secrets, VMs)

```sh
sed -e "s/@DISK_DIGEST@/<disk digest>/" -e "s|@SSH_PUBLIC_KEY@|$(cat ~/.ssh/id_ed25519.pub)|" instances.yaml > /tmp/140-instances.yaml
oc apply -f /tmp/140-instances.yaml
```

Secret missing at start (scenario): start `ci-east` before its Secret exists and record what KubeVirt reports.

```sh
virtctl start ci-east -n cloudinit-test
oc -n cloudinit-test get vm,vmi ci-east; oc -n cloudinit-test get events --field-selector involvedObject.kind=Pod | grep -i secret
virtctl stop ci-east -n cloudinit-test
```

Create both Secrets with a throwaway placeholder credential. It is a random string, not a Keycloak client, and authenticates to nothing:

```sh
umask 077; F=$(mktemp); python3 -c 'import secrets; print("fake-" + secrets.token_urlsafe(32))' > "$F"
for i in ci-west ci-east; do
  python3 -I scripts/vm-cloud-init/assemble_cloud_init_secret.py --instance $i --namespace cloudinit-test --allow-untracked --client-secret-file "$F"          # review the plan
  python3 -I scripts/vm-cloud-init/assemble_cloud_init_secret.py --instance $i --namespace cloudinit-test --allow-untracked --client-secret-file "$F" --apply
done
tr -d '\n' < "$F" | sha256sum > /tmp/140-fake-secret.sha256; rm -f "$F"
virtctl start ci-west -n cloudinit-test; virtctl start ci-east -n cloudinit-test
```

Evidence for each of `ci-west` and `ci-east`:

```sh
oc -n cloudinit-test get vm <i> -o yaml | grep -A3 cloudInitNoCloud       # only secretRef
oc -n cloudinit-test get vm <i> -o jsonpath='{.spec.template.spec.domain.firmware.uuid}'
virtctl ssh -n cloudinit-test cloud-user@vm/<i> -c '
  sudo bootc status | grep -i digest
  cat /etc/box1/site.env
  sudo cloud-init status --long; sudo cloud-init query instance-id
  sudo stat -c "%a %U:%G %n" /etc/box1/credentials /etc/box1/credentials/keycloak-client-secret
  test -r /etc/box1/credentials/keycloak-client-secret && echo READABLE || echo denied   # as cloud-user
  sudo -u box1-site sha256sum /etc/box1/credentials/keycloak-client-secret'
```

Expected: the same booted digest on both; `BOX1_SITE_ID=site_ds9` on `ci-west` and `site_spacedock` on `ci-east`; `750 root:box1-site` and `400 box1-site:box1-site`; `cloud-user` gets `denied`; `box1-site` reads a file whose `sha256sum` matches `/tmp/140-fake-secret.sha256`. Record hashes only.

Copies of the credential (security pass): count files that contain the fake secret and are readable by anyone other than root. Only the count is recorded; it must be 0.

```sh
virtctl ssh -n cloudinit-test cloud-user@vm/ci-west -c 'sudo find /var/lib/cloud /run/cloud-init /var/log /etc -xdev -type f -perm /o=r,g=r -print0 2>/dev/null | sudo xargs -0 grep -lF -f /root/fake 2>/dev/null | wc -l'
```

First, in an interactive SSH session, put the fake value in a root-only file without echoing it: `sudo sh -c 'umask 077; stty -echo; read -r V; stty echo; printf %s "$V" > /root/fake'`, then paste at the silent prompt. Delete `/root/fake` afterwards. Also check `sudo grep -cF -f /root/fake /var/log/cloud-init.log` is 0.

## 3. Rotation (approval: Secret update)

Assemble `ci-west` again with a new placeholder value, then `virtctl restart ci-west -n cloudinit-test`. Expected: the credential hash changes, `instance-id` does not, and `/var/log/cloud-init.log` shows `write_files` ran with frequency `always`. Also check that a guest `sudo reboot` alone does **not** pick up a Secret change made since the last VM start.

## 4. Re-create with data preserved (approval: VM deletion)

```sh
virtctl ssh -n cloudinit-test cloud-user@vm/ci-west -c '
  sudo mkfs.xfs -L box1data /dev/disk/by-id/virtio-data && sudo mkdir -p /mnt/data && sudo mount LABEL=box1data /mnt/data
  date -Is | sudo tee /mnt/data/marker; sudo sha256sum /mnt/data/marker; sudo umount /mnt/data
  sudo cloud-init query instance-id; ls -l /etc/ssh/ssh_host_ed25519_key.pub; ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub'
oc -n cloudinit-test get vm ci-west -o yaml > /tmp/ci-west-vm.yaml      # keep for re-create
oc -n cloudinit-test delete vm ci-west
oc -n cloudinit-test get dv ci-west-root ci-west-data                   # both must remain
oc apply -f /tmp/140-instances.yaml && virtctl start ci-west -n cloudinit-test   # the original manifest, not the dump, which pins firmware.uuid
```

Expected after the re-create: a new firmware UUID and `instance-id` (this verifies the KubeVirt behavior the runbook takes from source); `site.env` identical; the marker file and its hash unchanged; the SSH host key fingerprint unchanged. Then rebuild the root disk (delete `ci-west` and `ci-west-root`, re-create both) and expect identity re-applied, new host keys, and the data marker still intact.

## 5. Malformed user-data, upgrade and rollback

- **Malformed user-data:** replace `ci-east-cloud-init` with one whose `userdata` is invalid YAML and holds no credential: `oc -n cloudinit-test create secret generic ci-east-cloud-init --from-literal=userdata=$'#cloud-config\nwrite_files: [' --dry-run=client -o yaml | oc replace -f -`, restart `ci-east`, and record that the VM still boots, SSH works, `cloud-init status` reports the error, and the previous `site.env` remains. Re-assemble the real Secret afterwards; `--force-conflicts` lets the script take the field back from `oc replace`.
- **bootc upgrade keeps identity:** merge a trivial change to `cloudinit-check`, let it promote, then on `ci-west` run `sudo bootc switch --apply image-registry.openshift-image-registry.svc:5000/box1-ci/cloudinit-check@<new digest>` (or `bootc upgrade --apply` on the `:development` channel). Expect the new digest booted and `site.env` and the credential unchanged.
- **bootc rollback:** `sudo bootc rollback --apply`. Expect the old digest and the same identity.

## 6. Existing VMs untouched

```sh
oc -n legacy-erp-dev get vm legacy-erp -o jsonpath='{.metadata.annotations.box1\.org/os-image-digest}{"\n"}'
oc -n vm-golden-check-dev get vm vm-golden-check -o jsonpath='{.metadata.annotations.box1\.org/os-image-digest}{"\n"}'
gh api repos/box1-org/legacy-erp/commits/main -q .sha; gh api repos/box1-org/vm-golden-check/commits/main -q .sha
```

Compare with the baseline in `../evidence/01-discovery.md`. Expected: unchanged.

## 7. Clean up (approval: deletion)

```sh
oc delete namespace cloudinit-test
oc -n box1-ci delete rolebinding cloudinit-test-image-puller
```

Decommission `cloudinit-check` with the [service decommission runbook](../../../runbooks/service-decommission.md), or keep it as the cloud-init reference VM.
