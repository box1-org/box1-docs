# D-016 Which secrets integration

**Status:** resolved 2026-11-05 by the user: install Vault, later, tracked in box1-docs#41. The recommendation below was not taken. The user merged the service before this work, so the deployed database still uses the credential described in D-005.

**Observed in the cluster's catalogs:**

| Package | Catalog | Notes |
|---|---|---|
| `openshift-external-secrets-operator` v1.2.0 | Red Hat (`redhat-operators-v422`) | AllNamespaces install. Ships `passwords` and `clustergenerators` generator CRDs. |
| `external-secrets-operator` | Community, default channel `alpha` | Not Red Hat supported. |
| `vault-secrets-operator` | Certified | Needs a Vault server, and none exists. |
| `secrets-store-csi-driver-operator` | Red Hat | Needs an external store, and none exists. |

**Recommendation: `openshift-external-secrets-operator`.** Its Password generator can create the database password inside the cluster, with no external store and nothing in Git. An `ExternalSecret` then replaces the inline Secret in `workloads/order-service/postgres.yaml`.

**Not established:**

- Whether this operator installs and runs on this OpenShift 5.0 release candidate. Its catalog is labeled v4.22.
- Whether the generator works as described here. Nothing was installed, so behavior is from the CRD list only.
- Whether a generated password stays stable. `refreshInterval` must be set so it does not rotate on its own.

**Consequence for the live database:** PostgreSQL only reads its password at first initialization, so a new Secret does not change the existing role. The deployed database holds no order data. The choices are `ALTER ROLE` with the new password, or recreating the 5Gi volume. Recreating is destructive and needs separate approval, so `ALTER ROLE` is the plan.

**Wider issue:** the inline Secret comes from the template, so later services need this too. Updating `box1-templates` is out of this prompt's scope.
