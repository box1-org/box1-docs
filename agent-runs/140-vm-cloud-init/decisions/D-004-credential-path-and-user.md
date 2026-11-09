# D-004 Credential path, owner and service user

- `/etc/box1/site.env` 0644 `root:root`: non-secret settings, `KEY=value` lines with restricted characters (safe for systemd `EnvironmentFile=`).
- `/etc/box1/credentials/keycloak-client-secret` 0400 `box1-site:box1-site`: the client secret only, no trailing newline.
- `/etc/box1/credentials` 0750 `root:box1-site` (tmpfiles.d at boot).
- Service user `box1-site` (sysusers.d, no login shell). #126 has not named a site service user; site services should run as `User=box1-site`, or use `LoadCredential=` with `DynamicUser=`. If #126 picks another name, change `box1-site.conf` and the script's `SERVICE_USER` together.
- cloud-init keeps root-only copies of the user-data under `/var/lib/cloud/instances/*`; revocation includes `cloud-init clean` (runbook).
