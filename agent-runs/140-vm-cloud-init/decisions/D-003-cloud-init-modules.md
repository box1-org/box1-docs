# D-003 cloud-init runs only `write_files`, on every boot

Config: `rootfs-cloud-init/etc/cloud/cloud.cfg.d/90-box1.cfg`.

- `datasource_list: [ NoCloud, None ]`; `network: {config: disabled}`; `vendor_data: {enabled: false}`; `users: []`; `allow_public_ssh_keys: false`; `ssh_pwauth: false` (inert, because `set_passwords` does not run).
- `cloud_init_modules: [[write_files, always]]`; config and final lists empty.
- **Disabled, with reasons:** `ssh` (installs user-data `ssh_authorized_keys`/`ssh_keys` even with `allow_public_ssh_keys: false`; security pass finding 1), `users_groups` and `set_passwords` (accounts belong to the disk build and qemu-guest-agent `accessCredentials`), `bootcmd`/`runcmd`/scripts (no commands), `growpart`/`resizefs`/`disk_setup`/`mounts` (data disk untouched), `set_hostname`/`update_etc_hosts` (DHCP), `rh_subscription`/`yum_add_repo`/`package_update_upgrade_install` (bootc owns packages).
- **`write_files` frequency `always`:** a rotated Secret applies at the next VM restart without a new instance-id (cloud-init re-reads a disk seed on each boot; evidence/01).
- **Host keys:** `sshd-keygen@.service.d/zz-box1-keygen.conf` resets conditions (overriding upstream's "disable sshd-keygen while cloud-init is active") and restores the stock `ConditionFileNotEmpty=|!/etc/ssh/ssh_host_%i_key`, because `sshd-keygen` deletes existing keys before generating.
- **Not a security boundary:** user-data can override module lists, and boothooks/part-handlers run as root. Write access to `<instance>-cloud-init` is root in the guest; only the assembly script should write it.
- Coexistence with bootc: nothing under `/etc/box1` is in the image (build check), so the `/etc` three-way merge keeps it across upgrades; `bootc-fetch-apply-updates.timer` stays disabled; `box1-registry-setup.service` is unaffected (it is ordered on local disks, not cloud-init). **Not verified by a boot.**
