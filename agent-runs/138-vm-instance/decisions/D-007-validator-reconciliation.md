# D-007 Reconciling the #139 validator with the #140 bundle specification

These changes are in box1-gitops#134, on top of #133.

**Contract conflict:** #139's credential-key heuristic refused the #140 key `keycloakTokenUrl`, because the key contains the word `token`. Every #140-conformant instance failed `box1-gitops-validate` on the #133 head. The cross-check is in `evidence/03-cross-check.md`.

**Resolution:**
- The six #140 site keys skip the key-name test, for `<instance>-site` only. Their values are still checked.
- The #139 test fixture's site ConfigMap now uses the #140 keys.

**Rules added** (#140 asks that #139 did not enforce):
- `cloudinitdisk` is the only cloud-init volume, set with `secretRef` and nothing else;
- the `cloudinitdisk` disk exists;
- no `ds=` serial;
- `qemuGuestAgent` `accessCredentials` for `cloud-user` only;
- no user-data or network-data keys in Secrets;
- the `<instance>-site` ConfigMap is required and labelled, has no `binaryData`, and holds only the allowlisted keys and patterns.

**Added from the review pass:**
- exactly one `accessCredentials`, `volumes` and `disks` block;
- vm-instance Roles and bindings must match the generated set exactly;
- no ClusterRole or ClusterRoleBinding.

**Contract change:** `<instance>-site` is now **required**; #139 had called it optional.
