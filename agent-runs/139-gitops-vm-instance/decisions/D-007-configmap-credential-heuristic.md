# D-007 Site ConfigMap credential check

**Scope:** applies to every ConfigMap rendered in a vm-instance bundle, not only `<instance>-site`.

**Fails when any of the following holds:**
- A data or binaryData key, split into words on camelCase and `-`, `_`, `.`, contains one of: secret(s), password(s), passwd, pwd, passphrase, token(s), key(s), apikey, privatekey, credential(s), kubeconfig.
- A value contains a PEM private key.
- A value assigns a credential: `(password|passwd|pwd|secret|token|api[_-]?key|credentials?)` followed by `:` or `=` and a value.

**Accepted:** `keycloakUrl` and `keycloakClientId`. Word splitting avoids treating "key" inside "keycloak" as a credential word.

**Tradeoff:** `publicKey` or `sshKey` keys are rejected; SSH public keys belong in the admin Secret (VM rule). The value-assignment rule was added after review R-001.
