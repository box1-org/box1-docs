# Box1 manual installs and non-operator secrets

This runbook lists what was set up on the Box1 cluster by hand rather than by
Argo CD (`box1-org/box1-gitops` and `box1-org/box1-workloads-dev`) or by an
operator. Use it to plan a cluster rebuild, to choose what to move into GitOps
next, and to re-run the audit later. Secrets are listed **by name only**. This
document never records their values.

- **Snapshot:** 2026-11-05 23:22 EST (America/New_York)
- **Cluster:** OpenShift 5.0.0-rc.7 (Kubernetes v1.36.5), audited as user `mike`
- **Method:** read-only `oc get` calls; no cluster changes were made
- **GitOps reference:** `box1-gitops` `origin/main`. Local checkouts can be
  stale; one was missing `console-links` and `openshift-ai/operator`.
- **Backup:** cleaned YAML exports of these objects are in
  [`backup/`](backup/README.md). Secrets there are redacted templates; read
  the backup README before applying anything.

## How ownership was determined

| Signal | Interpretation |
| --- | --- |
| `argocd.argoproj.io/tracking-id` annotation | Managed by an Argo CD Application |
| `ownerReferences` or the `olm.owner` label | Created and reconciled by a controller or operator |
| `metadata.managedFields[0].manager` = `Mozilla` | Created in the OpenShift web console |
| `managedFields` manager = `kubectl-create`, `kubectl-client-side-apply`, `kubectl-patch` | Created with the CLI (`oc` or `kubectl`) |
| `managedFields` manager = `helm` | Created with the Helm CLI |
| `managedFields` manager = `catalog` or `odf-operator` | Created by OLM to resolve a dependency, so not manual |

The first `managedFields` entry identifies the creator. A later `Update` by
`Mozilla` or `kubectl-*` means someone also edited the object by hand.

## Re-running the audit

All of these commands are read-only. **Never print `.data` or
`.stringData` from Secrets**; the script below reads metadata only.

```sh
# Subscriptions: manual ones have no Argo tracking ID
oc get subscriptions.operators.coreos.com -A -o custom-columns=\
'NS:.metadata.namespace,NAME:.metadata.name,PKG:.spec.name,SRC:.spec.source,CH:.spec.channel,APPROVAL:.spec.installPlanApproval,CSV:.status.installedCSV,CREATED:.metadata.creationTimestamp,TRACK:.metadata.annotations.argocd\.argoproj\.io/tracking-id'

# Who created an object
oc get <kind> -n <ns> <name> --show-managed-fields \
  -o jsonpath='{range .metadata.managedFields[*]}{.manager}:{.operation} {end}'

# CatalogSources, Argo Applications, Helm releases
oc get catalogsources -n openshift-marketplace \
  -o custom-columns='NAME:.metadata.name,IMAGE:.spec.image,TRACK:.metadata.annotations.argocd\.argoproj\.io/tracking-id'
oc get applications.argoproj.io -n openshift-gitops
oc get secrets -A -l owner=helm   # Helm release records; check ownerReferences
```

Secret inventory, using metadata only:

```sh
cat > /tmp/secret-meta.py <<'EOF'
import json, sys
skip = {"kubernetes.io/service-account-token", "kubernetes.io/dockercfg", "helm.sh/release.v1"}
for i in json.load(sys.stdin)["items"]:
    m, t = i["metadata"], i.get("type", "")
    l, a = m.get("labels") or {}, m.get("annotations") or {}
    if t in skip or m.get("ownerReferences") or "olm.owner" in l \
       or a.get("openshift.io/owning-component"): continue
    mf = m.get("managedFields", [])
    print("\t".join([m["namespace"], m["name"], t, m["creationTimestamp"],
        "argo" if a.get("argocd.argoproj.io/tracking-id") else "-",
        mf[0].get("manager", "") if mf else "",
        ",".join(sorted({f.get("manager", "") for f in mf}))]))
EOF
oc get secrets -A -o json --show-managed-fields | python3 -I /tmp/secret-meta.py | sort | column -t -s $'\t'
```

The script output still includes secrets that platform operators generate in
`openshift-*` namespaces and secrets that cert-manager issues. Their creator is
an operator (for example `operator`, `virt-operator`, or
`cert-manager-certificates-issuing`), so leave them out when you classify.

## Operators installed by hand

Argo CD does not own these Subscriptions. All of them came from
`openshift-marketplace` catalogs.

| Operator (package) | Namespace | Catalog / channel | Approval | Installed CSV | Created (UTC) | Creator evidence |
| --- | --- | --- | --- | --- | --- | --- |
| OpenShift GitOps (`openshift-gitops-operator`) | `openshift-gitops-operator` | redhat-operators / latest | Manual | v1.22.2 | 2026-10-24 | `kubectl-client-side-apply` of [`box1-root/gitops-install.yaml`](https://github.com/box1-org/box1-gitops/blob/main/box1-root/gitops-install.yaml) |
| cert-manager (`openshift-cert-manager-operator`) | `cert-manager-operator` | redhat-operators / stable-v1 | Automatic | v1.20.1 | 2026-10-23 | console (`Mozilla`) |
| NVIDIA GPU Operator (`gpu-operator-certified`) | `nvidia-gpu-operator` | certified-operators-v422 / v26.7 | Manual | v26.7.2 | 2026-10-22 | console |
| Node Feature Discovery (`nfd`) | `openshift-nfd` | redhat-operators-v422 / stable | Automatic | 4.22.0 | 2026-10-22 | console |
| Kernel Module Management (`kernel-module-management`) | `openshift-kmm` | redhat-operators / stable | Automatic | v2.7.1 | 2026-10-22 | console |
| Web Terminal (`web-terminal`) | `openshift-operators` | redhat-operators / fast | Automatic | v1.17.2 | 2026-10-22 | console |
| LVM Storage (`lvms-operator`) | `openshift-lvm-storage` | redhat-operators-v422 / stable-4.22 | Manual | v4.22.0 | 2026-10-23 | console |
| OpenShift Data Foundation (`odf-operator`) | `openshift-storage` | redhat-operators / stable-4.22 | Automatic | v4.22.7-rhodf | 2026-10-23 | console |
| OpenShift Lightspeed (`lightspeed-operator`) | `openshift-lightspeed` | redhat-operators / stable | Automatic | v2.0.0 | 2026-11-02 | console |
| OpenShift Virtualization (`kubevirt-hyperconverged`) | `openshift-cnv` | redhat-operators / stable | Automatic | v5.0.0 | 2026-11-05 | console |

These OLM objects are **not** manual:

- **ODF component Subscriptions** (`cephcsi`, `mcg`, `ocs`, `rook-ceph`,
  `odf-dependencies`, and others) were created by `odf-operator` or by OLM
  `catalog`.
- **`devworkspace-operator`** was created by OLM as a dependency of Web
  Terminal and Dev Spaces.

### Operand CRs created by hand

None of these instances has an Argo tracking ID. On a rebuild, recreate them
after installing their operators.

| Kind / name | Namespace | Created (UTC) |
| --- | --- | --- |
| `ClusterPolicy/gpu-cluster-policy` | cluster | 2026-10-22 |
| `NodeFeatureDiscovery/nfd-instance` | `openshift-nfd` | 2026-10-22 |
| `LVMCluster/box1-storage` (`vg1` overprovisionRatio raised 1 → 2 on 2026-11-06) | `openshift-lvm-storage` | 2026-10-23 |
| `StorageCluster/ocs-storagecluster` | `openshift-storage` | 2026-10-25 |
| `HyperConverged/kubevirt-hyperconverged` | `openshift-cnv` | 2026-11-05 |

### Operators managed by GitOps (for comparison)

Argo CD Applications own these Subscriptions:

| Operator | Application |
| --- | --- |
| Advanced Cluster Security | `acs-operator` |
| Dev Spaces | `dev-spaces-operator` |
| Developer Hub | `developer-hub-operator` |
| AMQ Streams | `kafka-operator` |
| Pipelines | `pipelines-operator` |
| RH-SSO | `rhsso-operator` |
| Trusted Profile Analyzer | `rhtpa-operator` |
| OpenShift AI | `openshift-ai-operator` |

## Other manual installs and cluster configuration

### CatalogSources

| CatalogSource | Image | Creator |
| --- | --- | --- |
| `redhat-operators-v422` | `quay.io/rhpds/olm_snapshot_redhat_catalog:v4.22_2026_08_03` | console |
| `certified-operators-v422` | `registry.redhat.io/redhat/certified-operator-index:v4.22` | console |

Several Subscriptions depend on these catalogs: NFD, LVMS, NVIDIA GPU, Dev
Spaces, Developer Hub and OpenShift AI. Recreate the catalogs before those
Subscriptions. `rhtpa-redhat-current` is managed by Argo CD through
`rhtpa-operator`.

### Workloads installed without an operator or GitOps

| Object | Namespace | How | Notes |
| --- | --- | --- | --- |
| `Deployment/agent-sandbox-controller` and CRD `sandboxes.agents.x-k8s.io` | `agent-sandbox-system` | `kubectl apply` (2026-10-23) | Agent sandbox controller; the namespace also came from `kubectl apply`. Source manifest not recorded in a Box1 repo. |
| Helm release `openshell` (revision 4) | `openshell` | Helm CLI | Argo CD does not manage it; see `box1-gitops` `platform/openshell/MIGRATION.md`. The chart creates the `openshell` StatefulSet and Certificates. |
| `Deployment/vllm-test` | `vllm` | `kubectl apply`, then `kubectl set`/`patch` and console edits | Related to #26. |
| `Deployment/inventory-deployment` | `inventory-poc` | `kubectl apply` (2026-10-23) | Early proof of concept, separate from GitOps `inventory-service-dev`. |

These Helm releases are **not** manual. The `stackrox-central-services` and
`stackrox-secured-cluster-services` releases are owned by the ACS `Central` and
`SecuredCluster` CRs. The `rhtpa` release is owned by the
`TrustedProfileAnalyzer` CR. The `openshift-gateway-istiod` release belongs to
the cluster ingress operator.

### Node and machine configuration

| Object | How | Notes |
| --- | --- | --- |
| `KubeletConfig/box1-pod-density` (maxPods 400) and label `box1-pod-density=enabled` on MCP `master` | `kubectl apply` | Script in [`manual/kubelet-config.sh`](kubelet-config.sh) |
| `MachineConfig/10-ipmi-modules` | console | 2026-10-22 |
| `MachineConfig/11-i2c-core-builtin-override` | console | 2026-10-22 |

These MachineConfigs are **not** manual. The `50-*` chrony, dnsmasq and iSCSI
MachineConfigs came from the installer. `90-worker-swap-online` and the
`99-*-psi-karg` MachineConfigs are applied by OpenShift Virtualization
(`virt-platform-autopilot`).

### Certificates, ingress and authentication

| Object | How | Notes |
| --- | --- | --- |
| `ClusterIssuer/letsencrypt-production` | console | ACME with Cloudflare DNS-01 through `cert-manager/cloudflare-api-token` |
| `Certificate/openshift-api` in `openshift-config` | console | Issues `openshift-api-tls`, referenced by `APIServer cluster` `servingCerts` for `api.ocp.box1.org` |
| `Certificate/openshift-apps` in `openshift-ingress` | console | Issues `openshift-apps-tls`, the default IngressController certificate |
| OAuth identity provider `htpasswd` | console | Backed by `openshift-config/htpasswd-xtglx` |
| `Issuer/openshell-selfsigned`, `Issuer/openshell-ca-issuer` | Helm (`openshell`) | Not in GitOps |

## Secrets not managed by an operator

Names only. The "Value source" column describes where a value comes from; it
never contains the value.

### Created by hand (`kubectl` or the console)

| Namespace | Secret | Type | Creator | Purpose (inferred from name and consumer) |
| --- | --- | --- | --- | --- |
| `cert-manager` | `cloudflare-api-token` | Opaque | kubectl-create, console edit | Cloudflare API token for DNS-01 |
| `openshift-config` | `htpasswd-xtglx` | Opaque | console | htpasswd identity provider users |
| `openshift-devspaces` | `github-oauth-config` | Opaque | console | GitHub OAuth app for Dev Spaces |
| `openshift-pipelines` | `pipelines-as-code-secret` | Opaque | console | Pipelines-as-Code GitHub App credentials and webhook secret |
| `keycloak` | `keycloak-db-secret` | Opaque | kubectl-create | Keycloak PostgreSQL credentials |
| `keycloak` | `openshell-mike-initial-login` | Opaque | kubectl-create | Initial OpenShell realm user login |
| `rhdh` | `developer-hub-db` | Opaque | kubectl-create, kubectl-patch | Developer Hub PostgreSQL credentials |
| `rhdh` | `developer-hub-secrets` | Opaque | kubectl-create, console edit | Developer Hub app-config secrets |
| `rhdh` | `developer-hub-platform-secrets` | Opaque | kubectl-client-side-apply | Developer Hub platform integration credentials |
| `rhdh` | `dynamic-plugins-registry-auth` | Opaque | kubectl-create | Registry pull credentials for the onboarding plugin OCI image (see #38) |
| `stackrox` | `acs-oidc-config` | Opaque | kubectl-client-side-apply, kubectl-patch | ACS OIDC client configuration |
| `stackrox` | `admission-control-tls`, `collector-tls`, `sensor-tls` | Opaque | kubectl-client-side-apply | ACS cluster init bundle |
| `stackrox` | `tls-cert-admission-control`, `tls-cert-collector`, `tls-cert-sensor` | Opaque | kubectl-client-side-apply | ACS init bundle (newer secret names) |
| `vllm` | `admission-control-tls`, `collector-tls`, `sensor-tls` | Opaque | kubectl-client-side-apply (2026-10-26 21:38 UTC) | **Anomaly:** an ACS init bundle copy in the wrong namespace; no pod in `vllm` mounts it (checked 2026-11-05). See follow-ups. |
| `box1-ci` | `rhacs-ci` | Opaque | kubectl-client-side-apply | ACS API token for the CI security gates |
| `box1-ci` | `rhtpa-ci` | Opaque | kubectl-client-side-apply | TPA client credentials for SBOM upload |
| `box1-ci` | `redhat-registry-pull` | dockerconfigjson | kubectl-create | registry.redhat.io pull credentials for builds |
| `box1-ci` | `legacy-erp-deploy-ssh` | Opaque | kubectl-create | SSH deploy key for legacy ERP delivery |
| `asset-service-dev` | `asset-service-postgres` | Opaque | kubectl-create | Service database credentials |
| `fulfillment-adapter-dev` | `fulfillment-adapter-postgres` | Opaque | kubectl-create | Service database credentials |

### Created by Box1 bootstrap scripts

| Namespace | Secret | Creator | Purpose |
| --- | --- | --- | --- |
| `box1-ci` | `etc-pki-entitlement` | `box1-rhel-image-poc` | RHEL entitlement for image-mode builds |
| `trusted-profile-analyzer` | `rhtpa-ci` | `box1-rhtpa-bootstrap` | TPA CI OIDC client |
| `trusted-profile-analyzer` | `rhtpa-database` | `box1-rhtpa-bootstrap` | TPA PostgreSQL credentials |

### Created by the Helm CLI (`openshell` release)

| Namespace | Secret | Notes |
| --- | --- | --- |
| `openshell` | `openshell-credential-storage-key-encryption-key` | Encryption key for stored credentials. **Preserve it**: losing it makes stored credentials unreadable. |
| `openshell` | `openshell-jwt-keys` | JWT signing keys |

The `openshell-*-tls` secrets are issued by cert-manager from Certificates
that the chart creates.

### Managed by Argo CD (GitOps, not an operator)

| Namespace | Secret |
| --- | --- |
| `order-service-dev` | `order-service-postgres` |
| `inventory-service-dev` | `inventory-service-postgres` |
| `legacy-erp-dev` | `legacy-erp-admin-ssh`, `legacy-erp-deploy-ssh` |
| `vm-golden-check-dev` | `vm-golden-check-admin-ssh` |

### Created by the installer

`kube-system/kubeadmin`, `kube-system/kube-cloud-cfg`,
`openshift-config/pull-secret`,
`openshift-config/initial-service-account-private-key`,
`openshift-kube-apiserver-operator/next-bound-service-account-signing-key`,
`openshift-machine-api/master-user-data`,
`openshift-machine-api/worker-user-data`, and
`assisted-installer/assisted-installer-controller-secret`.

### Not listed

The audit left out these operator-managed secrets:

- Service-account tokens, dockercfg secrets and Helm release records.
- Anything with `ownerReferences`, including Argo CD, OLM and CR-owned
  secrets.
- Secrets issued by cert-manager.
- Secrets generated by platform operators: monitoring, OpenShift
  Virtualization, authentication, kube-apiserver, ingress, image registry,
  NooBaa and OpenShift AI.
- Per-user Dev Spaces secrets in `mike-devspaces`, which the Dev Spaces
  dashboard and DevWorkspace controller generate.

## Rebuild order

This order is inferred from the dependencies above and has **not been tested**
as a full rebuild.

1. Create the installer-provided secrets during installation. Then apply the
   htpasswd secret and the OAuth identity provider.
2. Apply `KubeletConfig/box1-pod-density`, label the master MCP, and apply the
   two console MachineConfigs. Wait for the MachineConfigPools to settle.
3. Create the `redhat-operators-v422` and `certified-operators-v422`
   CatalogSources.
4. Install NFD, KMM, NVIDIA GPU, LVMS and ODF, then create their operand CRs:
   `nfd-instance`, `gpu-cluster-policy`, `box1-storage` and
   `ocs-storagecluster`.
5. Install cert-manager. Create `cloudflare-api-token` and the
   `letsencrypt-production` ClusterIssuer, then the `openshift-api` and
   `openshift-apps` Certificates.
6. Apply `box1-root/gitops-install.yaml`, approve the InstallPlan, and apply
   the `box1-root` Application.
7. Before Argo CD syncs the dependent applications, create the hand-made
   secrets in this order:
   - `keycloak-db-secret`, `openshell-mike-initial-login`
   - the four `rhdh` secrets
   - `pipelines-as-code-secret`, `github-oauth-config`
   - the `box1-ci` secrets
   - the database secrets for `asset-service` and `fulfillment-adapter`
8. Generate a new ACS init bundle and apply it to `stackrox`. Create
   `acs-oidc-config`. Run the TPA bootstrap so it creates `rhtpa-ci` and
   `rhtpa-database`, and the RHEL image bootstrap so it creates
   `etc-pki-entitlement`.
9. Reinstall OpenShell with Helm using the preserved
   `openshell-credential-storage-key-encryption-key`. Then install Web
   Terminal, Lightspeed, OpenShift Virtualization and the agent-sandbox
   controller as needed.

Back up the hand-made secrets securely outside Git, for example in a password
manager. Never commit them to `box1-docs` or `box1-gitops`.

## Follow-ups (not done)

- **Move manually installed operators into `box1-gitops`.** Candidates:
  cert-manager and its ClusterIssuer and Certificates, LVMS, ODF, NFD, NVIDIA
  GPU, KMM, OpenShift Virtualization, Lightspeed, Web Terminal, the two
  CatalogSources, and the MachineConfigs and KubeletConfig.
- **Move OpenShell under Argo CD** following its `MIGRATION.md`.
- **Adopt a declarative secret mechanism** for the hand-made secrets, such as
  External Secrets or Sealed Secrets. Some service database secrets are created
  with kubectl and others by Argo CD; that split should be resolved.
- **Remove the stray ACS init-bundle secrets in `vllm`** after confirming
  nothing depends on them.
- **Decide whether to keep** `inventory-poc` and `vllm/vllm-test`. The latter
  is tracked under #26.
- **Source the agent-sandbox controller manifest from a repository** and record
  its version.

No backlog issues have been filed for these follow-ups yet, other than #26 and
#38 where noted.
