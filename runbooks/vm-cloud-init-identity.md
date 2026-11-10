# VM instance identity with cloud-init (NoCloud)

Use this runbook to give a RHEL image mode VM instance its site identity and machine credential, to rotate that credential, and to understand what happens when the VM or its disks are re-created. It covers the out-of-Git step that assembles the `<instance>-cloud-init` Secret.

Status, 2026-11-08 (America/New_York), [box1-docs#140](https://github.com/box1-org/box1-docs/issues/140):

- **Implemented and tested offline:** the `rhel-image-vm` template parameter `cloudInit`, its render checks, and the assembly script with its tests.
- **Not tested on the cluster:** no image with cloud-init has been built or booted yet, so nothing below about guest behavior has been observed. The live test plan is in [`agent-runs/140-vm-cloud-init/test-plan/`](../agent-runs/140-vm-cloud-init/test-plan/README.md). Treat the guest-side statements as the design until that plan has run.
- **Depends on:** instance bundles come from the `vm-instance` profile ([#138](https://github.com/box1-org/box1-docs/issues/138)), the validator rules from [#139](https://github.com/box1-org/box1-docs/issues/139), and real per-site Keycloak clients from [#131](https://github.com/box1-org/box1-docs/issues/131).

## How it works

One OS image (for example `site-gateway-os`) boots as several VMs. Each VM gets its identity from three places:

| Piece | Where it lives | Who manages it |
| --- | --- | --- |
| Site settings: `siteId` and endpoints | ConfigMap `<instance>-site`, in Git (`box1-workloads-dev/workloads/<instance>/`) | Argo CD |
| Machine credential: the Keycloak client secret | Only in the Secret `<instance>-cloud-init`, never in Git | An operator, with the script below |
| NoCloud disk | VirtualMachine volume `cloudinitdisk` with `cloudInitNoCloud.secretRef.name: <instance>-cloud-init` | Argo CD (the reference only) |

At each VM start, KubeVirt builds a NoCloud disk (label `cidata`) from the Secret's `userdata` key. In the guest, cloud-init writes two files from it:

| File | Mode and owner | Content |
| --- | --- | --- |
| `/etc/box1/site.env` | `0644 root:root` | `BOX1_INSTANCE`, `BOX1_SITE_ID`, `BOX1_KEYCLOAK_CLIENT_ID`, `BOX1_KEYCLOAK_TOKEN_URL`, optional `BOX1_ASSET_SERVICE_URL`, `BOX1_KAFKA_BOOTSTRAP_SERVERS`, `BOX1_OTLP_ENDPOINT`, and `BOX1_KEYCLOAK_CLIENT_SECRET_FILE` |
| `/etc/box1/credentials/keycloak-client-secret` | `0400 box1-site:box1-site` | The client secret only, with no trailing newline |

Site services run as `User=box1-site` and read the settings with `EnvironmentFile=/etc/box1/site.env`. They read the credential from the file named in `BOX1_KEYCLOAK_CLIENT_SECRET_FILE`, never from an environment variable. Services that use `DynamicUser=` can get the file through `LoadCredential=` instead.

### What cloud-init does in the image

The `rhel-image-vm` template adds cloud-init only when `cloudInit: true` (default `false`). The image's files come from the template's `rootfs-cloud-init/` tree:

| Setting | Effect |
| --- | --- |
| `datasource_list: [ NoCloud, None ]` | Never probes network metadata services. Without a NoCloud disk, it falls back to `None` and writes nothing |
| `network: {config: disabled}`, `vendor_data: {enabled: false}` | NetworkManager keeps DHCP on the pod network, as before. Vendor-data is ignored |
| `users: []`, `allow_public_ssh_keys: false`, `ssh_pwauth: false` | No default user. With the modules below, no account, group, sudo rule, password or SSH key is created or changed. `cloud-user` and its keys stay with the disk build and qemu-guest-agent `accessCredentials` |
| `cloud_init_modules: [[write_files, always]]`, empty config and final lists | Only `write_files` runs, on every boot. No `ssh`, `users_groups`, `set_passwords`, `bootcmd`, `runcmd`, scripts, packages, subscriptions, disks, mounts, growpart or hostname changes |
| `sshd-keygen@.service.d/zz-box1-keygen.conf` | Upstream cloud-init ships a drop-in that stops `sshd-keygen` while cloud-init is active. This override restores the stock condition, so `sshd-keygen` still creates missing host keys and never replaces existing ones |
| `tmpfiles.d/box1-site.conf` | Creates `/etc/box1/credentials` as `0750 root:box1-site` at boot |
| `sysusers.d/box1-site.conf` | The `box1-site` system user, with no login shell |

The image build fails if the image ships anything under `/etc/box1`.

**This is not a security boundary.** The module lists shape what Box1-generated user-data does. Other user-data can override them, and `#cloud-boothook` or part-handler parts run as root before any module list applies. Anyone who can write the `<instance>-cloud-init` Secret is root in that guest, as anyone who can edit `<instance>-admin-ssh` already is. Only the assembly script below should write the Secret. A check that the Secret's user-data contains only the two `write_files` entries (for example an admission policy on Secrets labelled `box1.org/cloud-init`) is a possible follow-up for #138/#139.

## Instance bundle specification (for #138 and #139)

The `vm-instance` bundle in `box1-workloads-dev/workloads/<instance>/` adds these to the VM golden-path resources:

```yaml
# virtualmachine.yaml (excerpt)
spec:
  template:
    spec:
      accessCredentials:            # unchanged: qemuGuestAgent, users [cloud-user]
        - sshPublicKey:
            source: {secret: {secretName: <instance>-admin-ssh}}
            propagationMethod: {qemuGuestAgent: {users: [cloud-user]}}
      domain:
        devices:
          disks:
            # root, serviceca and regtoken as in rhel-image-vm, plus:
            - name: cloudinitdisk
              disk: {bus: virtio}
      volumes:
        # root, serviceca and regtoken as in rhel-image-vm, plus:
        - name: cloudinitdisk
          cloudInitNoCloud:
            secretRef:
              name: <instance>-cloud-init
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: <instance>-site
  namespace: <instance>-dev
  labels:
    box1.org/instance: <instance>
data:
  siteId: site_ds9                       # required, ^[a-z][a-z0-9_]{1,62}$
  keycloakClientId: site-west            # required, ^[a-z][a-z0-9-]{1,62}$
  keycloakTokenUrl: https://<keycloak-host>/realms/box1/protocol/openid-connect/token   # required, https
  assetServiceUrl: https://<asset-service-host>     # optional, https
  kafkaBootstrapServers: <host>:<port>[,<host>:<port>]   # optional
  otlpEndpoint: http://<collector>:4318  # optional, http or https
```

Validator rules for `vm-instance` workloads, to be implemented by #139 in `gitops-validate` (and mirrored by #138 in the plugin's bundle check):

1. The VirtualMachine has exactly one cloud-init volume. It is named `cloudinitdisk`, uses `cloudInitNoCloud`, and sets only `secretRef.name: <instance>-cloud-init`. It has no `userData`, `userDataBase64`, `networkData`, `networkDataBase64` or `networkDataSecretRef`, and there is no `cloudInitConfigDrive` volume. A disk named `cloudinitdisk` exists.
2. No rendered manifest contains `userData:` or `userDataBase64:`, and the bundle contains no Secret named `<instance>-cloud-init` or with a `userdata`/`userData` key. That Secret is created outside Git.
3. `accessCredentials` stays `qemuGuestAgent` for `cloud-user` only; `noCloud` propagation is refused.
4. ConfigMap `<instance>-site` exists, is labelled `box1.org/instance: <instance>`, has no `binaryData`, has only the six keys above, has the three required ones, and each value matches its pattern. URLs carry no user info (`@`), no query string (`?`), no spaces, quotes or `$`. The assembly script applies the same allowlist and patterns.
5. The general secret rules still hold: only SSH public keys in `<instance>-admin-ssh`, and an empty updater token Secret.

Readiness (#138): the VM stays `Halted` until the Secret exists. Kubernetes RBAC cannot grant metadata-only access to a Secret, so a platform check that looks for it either holds `get` on that one Secret (`resourceNames: [<instance>-cloud-init]`) and requests `PartialObjectMetadata` so the data is never transferred or logged, or relies on the VMI's start failure. Pick one in #138 and record it.

## Provision a new instance

Approval is required: creating a Secret is a credential action. Never paste the secret into a command line, chat, issue or log.

Prerequisites:

- The instance bundle is merged and synced, so the ConfigMap `<instance>-site` exists in `<instance>-dev`, and the VM is `Halted`.
- The instance's Keycloak client exists (#131), and you can read its secret from the approved source.
- `oc` is logged in as a user who may create Secrets in `<instance>-dev`. Python 3.9 or newer.

1. Put the client secret in a private file, or in an environment variable without echoing it:

   ```sh
   umask 077
   SECRET_FILE=$(mktemp)
   read -rs V && printf '%s' "$V" > "$SECRET_FILE"; unset V   # paste at the silent prompt; printf is a shell builtin
   ```

   The file must be a regular file you own with mode 0600; symlinks are refused. `--client-secret-env NAME` also works, and the script never passes that variable on to `oc`, but an exported variable reaches every other child of your shell, so prefer the file.

2. Review the plan. The script reads the ConfigMap from the cluster and contacts nothing else:

   ```sh
   python3 -I scripts/vm-cloud-init/assemble_cloud_init_secret.py \
     --instance site-west --client-secret-file "$SECRET_FILE"
   ```

   Check that `site.env` shows the expected `BOX1_SITE_ID` and endpoints, that the credential is `<redacted>`, and that the target is `site-west-dev/site-west-cloud-init`. The script refuses a ConfigMap without an Argo CD tracking annotation, because it did not come from Git (`--allow-untracked` exists for test namespaces only). Also confirm the instance's Argo CD Application is `Synced`, so the live ConfigMap matches Git: the token URL decides where the guest sends its credential.

3. Optionally, validate on the server without storing anything: add `--server-dry-run`.
4. Apply: add `--apply`. The script runs `oc apply --server-side --force-conflicts --field-manager=box1-cloud-init-assembler -f -` with the manifest on stdin. It takes back any field changed by hand. Server-side apply leaves no `last-applied-configuration` copy of the data in an annotation; if an old Secret has one (from a client-side `oc apply`), remove it with `oc annotate secret <instance>-cloud-init kubectl.kubernetes.io/last-applied-configuration-`, because it holds the old credential.
5. Delete the temporary file: `rm -f "$SECRET_FILE"`.
6. Start the VM through its normal GitOps path (the first promotion sets `runStrategy: Always`).

The Secret is labelled `box1.org/instance: <instance>` and `box1.org/cloud-init: userdata`, and annotated with `box1.org/site-config-sha256`, a hash of the ConfigMap data only. It carries no Argo CD tracking label, so Argo neither manages nor prunes it.

## Verify in the guest

```sh
virtctl ssh -n <instance>-dev cloud-user@vm/<instance>
sudo cloud-init status --long          # expect "status: done", datasource DataSourceNoCloud
cat /etc/box1/site.env                 # the expected BOX1_SITE_ID
sudo stat -c '%a %U:%G %n' /etc/box1/credentials /etc/box1/credentials/keycloak-client-secret   # expect 750 root:box1-site, 400 box1-site:box1-site
test -r /etc/box1/credentials/keycloak-client-secret && echo READABLE || echo denied             # as cloud-user: expect denied
sudo -u box1-site test -r /etc/box1/credentials/keycloak-client-secret && echo readable-by-box1-site
sudo bootc status                      # booted image digest
```

Never `cat` the credential, as any user, in a shared terminal or a recorded session; test access with `test -r`.

cloud-init also keeps root-only copies of the raw user-data, which include the credential: `/var/lib/cloud/instances/<instance-id>/user-data.txt*`, `cloud-config.txt` and `obj.pkl`, and `/run/cloud-init/` while running. An old instance-id directory keeps the old credential after a VM re-create. They are readable only by root, which meets the requirement, but they matter for revocation (below).

## Rotate the credential

1. Rotate the client secret at the source (Keycloak, #131).
2. Re-run the provisioning steps 1–5 with the new value. Only the Secret changes.
3. Restart the VM (`virtctl restart <instance> -n <instance>-dev`). This is needed because KubeVirt builds the NoCloud disk when the VM starts, so a guest `reboot` reuses the old disk.
4. In the guest, check that the credential file changed (compare `sudo sha256sum` before and after, without printing the file) and that the site service authenticates with the new secret.

This works without a new instance-id because the image runs `write_files` on every boot. cloud-init re-reads a disk-based NoCloud seed at each boot (cloud-init 24.4 `DataSourceNoCloud.check_instance_id` does not trust its cache for a disk seed), so the new user-data is used. **Not tested on the cluster.**

## Re-create, rebuild and upgrade

The cluster runs OpenShift Virtualization 5.0.0 with KubeVirt operator v1.9.0 (observed). In the KubeVirt `release-1.9` source, the NoCloud `instance-id` is the VMI's firmware UUID, and the VM webhook assigns a random `spec.template.spec.domain.firmware.uuid` when a VirtualMachine is created; the VM keeps it from then on. On the cluster, `vm-golden-check` has a stored firmware UUID that is not the legacy name-derived value. **The guest-visible instance-id and the re-create behavior are not verified yet** (test plan step 4).

| Event | instance-id | `write_files` (identity files) | SSH host keys (`sshd-keygen`) |
| --- | --- | --- | --- |
| Guest reboot | Same | Rewritten from the same NoCloud disk | Kept |
| VM restart (stop and start) | Same | Rewritten from the Secret's current content | Kept |
| VirtualMachine deleted and re-created, root disk kept | New (new firmware UUID), unless the manifest pins `firmware.uuid` | Rewritten | Kept |
| Root disk rebuilt (new DataVolume) | New | Written | New keys generated |
| `bootc upgrade` or `bootc rollback` | Same | Rewritten at the next boot | Kept |
| NoCloud disk removed | Datasource `None` (`iid-datasource-none`) | Nothing written; **old files stay** | Kept |

Consequences:

- Identity always follows the Secret at the last VM start. Local edits to `/etc/box1/site.env` are overwritten at the next boot.
- `/etc/box1/` is not in the image, so the bootc `/etc` three-way merge keeps it across upgrades and rollbacks. An image must never ship files under `/etc/box1/site.env` or `/etc/box1/credentials/`; the template's build check refuses them.
- Removing the disk does not revoke anything. To revoke a credential, disable or rotate the client in Keycloak first. Then, in the guest, delete the file and cloud-init's copies: `sudo rm -f /etc/box1/credentials/keycloak-client-secret && sudo cloud-init clean` (this also resets the instance state; the next boot runs as a new instance).
- If the Secret is missing when the VM starts, the VM is expected not to start, because the Secret is mounted into its virt-launcher pod. The exact status KubeVirt reports has not been observed; it is in the test plan.

## Data disk

cloud-init never manages disks here: `disk_setup`, `mounts`, `growpart` and `resizefs` are not in the module lists, so user-data cannot partition, format or mount anything. A site's data disk must be a separate DataVolume or PVC, never a `dataVolumeTemplates` entry (`gitops-validate` already refuses those), so deleting and re-creating the VirtualMachine keeps it. Mount it from the image, for example with a systemd mount unit by filesystem label. That belongs to the site image (#126), not to cloud-init.

## Roll back or remove

- **Template:** revert the `box1-templates` PR. Repositories generated with `cloudInit: false` never contained cloud-init, so they are unaffected.
- **One instance:** remove the `cloudinitdisk` disk and volume from the VM through GitOps, then `oc delete secret <instance>-cloud-init -n <instance>-dev` (approval required). The guest keeps the last written files until you delete them.
- **An image built with cloud-init:** to stop cloud-init without a rebuild, create `/etc/cloud/cloud-init.disabled` in the guest. To remove it, rebuild the image with `cloudInit: false` and upgrade.

## Tests

- Template render checks: `npm run validate` in `box1-templates`; `VM_BASELINE_REF=origin/main npm run validate` also proves `cloudInit: false` renders byte-identical to that revision.
- Assembly script, offline, with a generated fake secret and a fake `oc`: `python3 -I scripts/vm-cloud-init/test_assemble_cloud_init_secret.py -v`.
- Live boot tests: [`agent-runs/140-vm-cloud-init/test-plan/`](../agent-runs/140-vm-cloud-init/test-plan/README.md). **Not run.**
