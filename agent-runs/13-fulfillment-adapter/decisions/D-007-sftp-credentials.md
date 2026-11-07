# D-007 SFTP key and known-hosts provisioning

**Status:** **open: approval required**.

**Gap:** no secret store (#41).

**Options:**
- A (recommended) a Secret `fulfillment-adapter-sftp` created out of band by the user, never in Git, with keys `id_ed25519` and `known_hosts` (the VM's host key). The Deployment mounts it read-only with `optional: true`; the adapter keeps SFTP disabled and accepts work durably until it is present. Host-key rotation: #25 publishes the new key; `known_hosts` carries old and new during the change; pod restart.
- B wait for Vault (#41).

**Consequences:** No in-cluster dispatch is possible until A is approved and the VM exists. Strict host-key checking is always on; there is no accept-new mode in code.
