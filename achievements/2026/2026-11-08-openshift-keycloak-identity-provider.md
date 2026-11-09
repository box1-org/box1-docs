# OpenShift: Keycloak as a cluster identity provider

**Date:** 2026-11-08 (America/New_York)
**Status:** Complete. The Keycloak client is GitOps-managed; the OAuth identity provider and its secret are deliberately manual.

## Outcome

The OpenShift login page now offers three choices: `keycloak`, `htpasswd`, and `kube:admin`. Users in the Keycloak `box1` realm can sign in to the web console and `oc login --web` with their Keycloak credentials. A Keycloak sign-in as `mike` links to the existing OpenShift user `mike`, which keeps its `cluster-admin` binding. The htpasswd provider and the kubeadmin user are unchanged.

This puts the cluster on the same identity source already used by Developer Hub, OpenShell, the operations console and the Box1 service APIs ([RHDH Keycloak OIDC](2026-11-05-rhdh-keycloak-oidc.md)).

## Starting baseline

- `OAuth/cluster` had a single identity provider, `htpasswd` (`mappingMethod: claim`, secret `openshift-config/htpasswd-xtglx`), created in the console. `kubeadmin` was also available.
- OpenShift user `mike` had one identity, `htpasswd:mike`, and was the only user with a `cluster-admin` ClusterRoleBinding.
- Keycloak (RH-SSO operator, realm `box1`, `https://keycloak.apps.ocp.box1.org`) had no client for OpenShift. Its TLS certificate comes from the `letsencrypt-production` ClusterIssuer, so the OAuth server trusts it without a CA ConfigMap.
- The realm contained users `mike`, `claude`, and `loser`. Keycloak `mike` collided with the htpasswd user `mike`, so the default `claim` mapping would have rejected that login.

## What changed

| Change | Where | Managed by |
| --- | --- | --- |
| Confidential `KeycloakClient` `openshift` (authorization code flow only, no service account, `fullScopeAllowed: false`, default scopes `profile` and `email`). Redirect URI: `https://oauth-openshift.apps.ocp.box1.org/oauth2callback/keycloak` | `box1-gitops` `platform/identity/keycloak/realm/openshift-client.yaml`, [box1-gitops#131](https://github.com/box1-org/box1-gitops/pull/131), merge commit `4bcc907` | Argo CD application `keycloak` |
| Secret `openshift-config/keycloak-openshift-client`, key `clientSecret`, copied from the operator-generated `keycloak/keycloak-client-secret-openshift` (`CLIENT_SECRET`) without printing it | Cluster | Manual (`oc create … \| oc apply`) |
| Identity provider `keycloak` added to `OAuth/cluster` with a JSON-patch `add`, leaving `htpasswd` untouched: type `OpenID`, issuer `https://keycloak.apps.ocp.box1.org/auth/realms/box1`, client `openshift`, claims `preferred_username` / `name` / `email`, extra scopes `email` and `profile`, `mappingMethod: add` | Cluster | Manual (`oc patch`) |

**Decisions:**

- **`mappingMethod: add`** (user choice). A Keycloak identity links to an existing OpenShift user with the same `preferred_username`, so Keycloak `mike` and htpasswd `mike` are one user. The tradeoff: any future Keycloak username that matches an existing OpenShift user gets that user's permissions, so creating realm users is effectively privileged. Keycloak users without a match become new users with no extra role bindings.
- **OAuth stays manual** (user choice). Argo CD does not manage `OAuth/cluster` today, and the user chose not to move it. The [manual-installs runbook](../../manual/manual-installs-and-secrets.md) and its [backup export](../../manual/backup/cluster-config/oauth.yaml) now record the provider, the secret, and the rebuild step.

## Validation and evidence

| Check | Expected | Result |
| --- | --- | --- |
| Argo CD `keycloak` after the merge | Synced at `4bcc907`, Healthy | Synced, Healthy |
| `KeycloakClient/openshift` | Ready; operator creates the client secret | `ready: true`; `keycloak-client-secret-openshift` has `CLIENT_ID` and `CLIENT_SECRET` |
| Authentication ClusterOperator after the patch | New `oauth-openshift` pod, not degraded | Available, not Progressing, not Degraded; no errors in the OAuth server logs from the following 30 minutes |
| Login selection page | Lists all three providers | `idp=htpasswd`, `idp=keycloak`, `idp=kube:admin` |
| `oauth/authorize?idp=keycloak` | Redirect to the `box1` realm with client `openshift` and the `/oauth2callback/keycloak` redirect URI | Redirect matches; Keycloak sign-in page returns HTTP 200 |
| Real browser sign-in as Keycloak `mike` (done by the user) | Linked to existing user `mike` | User `mike` now has identities `htpasswd:mike` and `keycloak:d82ec2dc-…` (created 2026-11-08 22:28 EST); no new user was created |
| `oc apply --dry-run=server` and `oc diff` of the updated `manual/backup/cluster-config/oauth.yaml` | Matches live | No diff |

**Not tested:** htpasswd and kubeadmin sign-in after the change (the htpasswd provider and identity were not modified), sign-in by other realm users (`claude`, `loser`), and `oc login --web` from the CLI.

## Final operational state

- `OAuth/cluster` identity providers: `htpasswd` (`claim`) and `keycloak` (`OpenID`, `add`), plus kubeadmin. Managed by hand; not in `box1-gitops`.
- `keycloak/KeycloakClient/openshift`: Argo CD from `box1-gitops` `main`.
- `openshift-config/keycloak-openshift-client`: hand-made copy of the operator-generated secret. If Keycloak or the client is recreated, the secret changes and must be copied again or Keycloak sign-in fails.
- Recorded in the [manual-installs runbook](../../manual/manual-installs-and-secrets.md) (authentication table, secrets table, rebuild order step 8) with a redacted template in [`manual/backup/secrets/openshift-config.yaml`](../../manual/backup/secrets/openshift-config.yaml).

## Recovery and follow-ups

**Remove the provider** (htpasswd and kubeadmin keep working):

```sh
# find the index of the keycloak entry, then remove it
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\n"}{end}'
oc patch oauth cluster --type=json -p '[{"op":"remove","path":"/spec/identityProviders/1"}]'
oc delete secret keycloak-openshift-client -n openshift-config
oc delete identity keycloak:d82ec2dc-55f5-4309-9606-97bda4d9a959   # unlinks the Keycloak login from user mike
```

Then revert `openshift-client.yaml` and its `kustomization.yaml` entry in `box1-gitops`. This rollback was **not exercised**.

**Rotate the client secret:** regenerate it in Keycloak (or let the operator recreate the client), then re-copy `CLIENT_SECRET` into `openshift-config/keycloak-openshift-client`. The OAuth server picks up the change on its own rollout.

**Follow-ups:**

- No backlog issue was filed. Moving `OAuth/cluster` into GitOps was offered and declined; it remains listed among the manual objects in the runbook.
- Consider group-based access for Keycloak users (for example a `groups` claim mapped to OpenShift groups) before adding more realm users, since `mappingMethod: add` relies on username matching. Not planned.
