# Site Expansion back-out

This procedure removes the Site Expansion epic ([box1-docs#126](https://github.com/box1-org/box1-docs/issues/126)) and its golden-path prerequisites (#136–#141). It returns Box1 to the state captured by the tag `pre-site-expansion-2026-11-09`, while keeping the unrelated work that landed afterwards.

> **Status: written 2026-11-10 (America/New_York), not exercised.** Every step is an approval item: these steps delete running VMs, namespaces, credentials and GitHub repositories. Run a level only on the owner's instruction, and record the outcome in the execution log at the end of this file.

## The tags

Each tag is annotated and points at the last commit on `main` before #126 was filed (2026-11-09T02:30:46Z).

| Repository | `pre-site-expansion-2026-11-09` | `main` when this was written |
|---|---|---|
| `box1-templates` | `5663eb3` | `c074564` |
| `box1-gitops` | `8e298a6` | `372545b` |
| `box1-workloads-dev` | `937ccb3` | `50a8aa9` |
| `box1-docs` | `757a28a` | `69cddcd` |

- **Repositories created by the expansion:** `site-gateway` and `site-gateway-os` did not exist before it, so they have no tag.
- **Repositories not tagged:** every other `box1-org` repository has no expansion commits on `main`, so none is tagged. The open edge-sites PRs are covered in step 0.

**Do not reset `main` to a tag.** Unrelated work landed after the cutoff, and a reset would lose it:

| Repository | Unrelated work after the cutoff (keep it) |
|---|---|
| `box1-gitops` | Builder image (#130), Keycloak OpenShift client (#131), Lightspeed CPU (#137), OpenShift AI removal (#138), Hub TLS trust (#139), Langfuse (#142, #144, #145, #148) |
| `box1-workloads-dev` | Promotions of `agentic-operations`, `order-service` and `fulfillment-adapter`; Langfuse traces (#214) |
| `box1-docs` | Keycloak IdP, legacy-erp, Dev Spaces, CPU right-sizing and Langfuse achievement logs |
| Other repositories | All their later commits are unrelated (for example agentic-operations' LangChain4j work) |

`box1-templates` is the only repository whose later commits all belong to the expansion. There, restoring the tag's tree is equivalent to reverting them.

`git diff pre-site-expansion-2026-11-09 main` in a repository shows exactly what has changed since the tag.

## What the expansion added

**Golden path (code)**

| Repository | PRs | Effect |
|---|---|---|
| `box1-templates` | #33, #34, #37, #39, #40 | Onboarding plugin: dispatch table, then the `artifact` and `vm-instance` profiles (1.3.0 → 1.5.2). Templates `quarkus-monorepo` and `vm-instance`. `rhel-image-vm` gained an optional `cloudInit` parameter, off by default |
| `box1-gitops` | #132, #133, #134, #140, #141, #143 | `gitops-validate` gains the `vm-instance` and `ci/` rules; `gitops-promote` gains an `instance-name` target. New Tasks `box1-maven-bundle`, `box1-bundle-consumer-pr` and `box1-bootc-status`. `box1-bootc-build` gains a route login, plus the `ci-bundle-pull` ServiceAccount and its token. The Hub onboarding Role gains read access to `imagestreams` and `imagestreamimages` (`platform/developer-hub/onboarding/access.yaml`) |
| `box1-gitops` | #136, #147, #149 | Plugin pins 1.5.0 → 1.5.1 → 1.5.2 (`dynamic-plugins.yaml`, `backstage.yaml`) |
| `box1-gitops` | #146 | KeycloakClients `site-west` and `site-east` |

**Workloads**

| Workload | Where | Created by |
|---|---|---|
| `site-gateway` (code-only, `artifact`) | GitHub repository; `box1-workloads-dev` `ci/site-gateway/` and `applications/site-gateway-ci.yaml`; in `box1-ci`: PAC Repository, `site-gateway-release` ServiceAccount, `site-gateway-bundle` ImageStream, push Role | Hub onboarding (#205) |
| `site-gateway-os` (`virtual-machine`) | GitHub repository; `workloads/site-gateway-os/`; namespace `site-gateway-os-dev` and its VM; in `box1-ci`: PAC Repository and ImageStreams `site-gateway-os` and `site-gateway-os-disk` | Hub onboarding (#201, #203) |
| `site-west`, `site-east` (`vm-instance`) | `workloads/site-*/`; namespaces `site-*-dev` with their VMs and root disks; `<site>-cloud-init` Secrets (outside Git) | Hub onboarding (#220, #221, #222, #224) |

**Outside Git**

| Object | Where | Notes |
|---|---|---|
| `vm-instance-status-ssh` | `box1-ci` Secret | Booted-digest key. Its public half is baked into `site-gateway-os` (`SHA256:o3i07lRy…`) |
| `site-west-cloud-init`, `site-east-cloud-init` | Site namespaces | Assembled by box1-docs#147's script. Removed with each namespace |
| `keycloak-client-secret-site-west` and `-site-east` | `keycloak` | Created by the operator from the KeycloakClients |
| Onboarding records | `rhdh` ConfigMaps and Leases `box1-onboard-{site-west,site-east,site-gateway,site-gateway-os}` | Hub onboarding state |
| Catalog entities and Locations | Developer Hub | `component:default/site-west`, `site-east`, `site-gateway`, `site-gateway-os`; templates `quarkus-monorepo` and `vm-instance` |

The Hub ran plugin 1.2.0 at the tag. Its pin was `sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b`, revision `8537ec131d6afc49bde020f6e110aa9073bdb0ac`.

## Choose a level

The levels are cumulative. Each one leaves the platform working; stop at the lowest level that solves the problem.

| Level | Removes | Keeps |
|---|---|---|
| **1. Sites** | `site-west`, `site-east`, and their Keycloak clients | The golden-path capability, `site-gateway`, `site-gateway-os` |
| **2. Site software** | Level 1, plus `site-gateway`, `site-gateway-os` and their repositories, images and CI | The new templates and plugin profiles, unused |
| **3. Golden path** | Level 2, plus plugin 1.5.x → 1.2.0, the two templates, `rhel-image-vm` `cloudInit`, and the GitOps Task, validator and RBAC changes | Nothing from the expansion except documentation and issues |

## 0. Before any level

1. **Freeze in-flight expansion work.** Do not merge these, and close them if backing out past the level they need. At the time of writing:

   | Repository | PRs |
   |---|---|
   | `site-gateway-os` | #6, #7 |
   | `site-gateway` | #1 |
   | `box1-workloads-dev` | #223, #225 |
   | `box1-gitops` | #150, #151, #152 |
   | `asset-service` | #8 |
   | `inventory-service` | #7 |
   | `operations-console` | #17 |
   | `box1-ops-contracts` | #14 |
   | `box1-docs` | #145, #146, #147, #148 (documentation only) |

   List the current set:

   ```bash
   for r in $(gh repo list box1-org --limit 100 --json name --jq '.[].name'); do gh pr list --repo box1-org/$r --state open --json number,title,headRefName --jq '.[]|select(.headRefName|test("edge-sites|site-|golden-path|agent-run/1[34]|bundle/"))|"'$r'#\(.number) \(.title)"'; done
   ```
2. **No onboarding is running.** Every `rhdh/box1-onboard-*` Lease has an empty holder:

   ```bash
   oc get lease -n rhdh -o custom-columns=NAME:.metadata.name,HOLDER:.spec.holderIdentity | grep box1-onboard
   ```
3. **Record the starting state.** These reads are the evidence for the execution log:

   ```bash
   oc get vm -A | grep -E 'site-|legacy-erp|vm-golden-check'
   oc get application -n openshift-gitops | grep -E 'site-|developer-hub|pipelines-ci|keycloak'
   for r in box1-templates box1-gitops box1-workloads-dev; do gh api repos/box1-org/$r/commits/main --jq '"'$r' \(.sha)"'; done
   ```
4. **Wait between merges.** Leave about 10 s between merges (#64), and watch for stranded PAC runs. A finished run that still has `pipelinesascode.tekton.dev/state: started` blocks its repository's queue. Recover it with the annotate step recorded on #64.

## Level 1: remove the sites

Use [Service decommissioning](service-decommission.md), section **Virtual machines → `vm-instance` specifics**, for each site.

1. **One PR in `box1-workloads-dev`** removes `applications/site-west.yaml`, `applications/site-east.yaml`, `workloads/site-west/` and `workloads/site-east/`. Merge it after `box1-gitops-validate` and `box1-phase1-smoke` pass.
2. **Remove each site from the cluster.**
   1. Hard-refresh the parent Application `box1-workloads-dev`, and wait until it shows the merge commit.
   2. For each site, add the resources finalizer to its Application and delete it:

      ```bash
      oc -n openshift-gitops patch application <site> --type=merge -p '{"metadata":{"finalizers":["resources-finalizer.argocd.argoproj.io"]}}'
      oc -n openshift-gitops delete application <site> --wait=false
      ```

      This cascade removes `<site>-dev`, including the VM, the root disk and its PV, and the cloud-init Secret. It also removes `box1-ci/<site>-image-puller` and the `openshift-gitops` observer Role.
3. **Clear the Hub state.** Delete the onboarding records:

   ```bash
   oc -n rhdh delete configmap,lease box1-onboard-site-west box1-onboard-site-east
   ```

   Delete the catalog Locations whose target is `https://github.com/box1-org/box1-workloads-dev/{tree,blob}/main/workloads/<site>/catalog-info.yaml`, as in step 3 of the decommission runbook.
4. **Remove CI leftovers.** Delete the booted-digest PipelineRuns:

   ```bash
   oc -n box1-ci delete pipelineruns -l backstage.io/kubernetes-id=site-west
   oc -n box1-ci delete pipelineruns -l backstage.io/kubernetes-id=site-east
   ```
5. **Revoke the credentials.** Revert box1-gitops#146 in a `box1-gitops` PR. The `keycloak` Application has `prune: false`, so the KeycloakClients stay until they are deleted by hand. Deleting them revokes the credential the guests held:

   ```bash
   oc -n keycloak delete keycloakclient site-west site-east
   ```

   Check that `keycloak-client-secret-site-west` and `-site-east` are gone, then check that a client-credentials token request for `site-west` fails.
6. **Verify.**
   - No `site-west-dev` or `site-east-dev` namespace, and no `site-west` or `site-east` Application.
   - `site-gateway-os`, `legacy-erp` and `vm-golden-check` are still `Running`.

## Level 2: remove `site-gateway` and `site-gateway-os`

Do Level 1 first: the sites boot `site-gateway-os`'s disk.

1. **One PR in `box1-workloads-dev`** removes:
   - `applications/site-gateway-os.yaml` and `workloads/site-gateway-os/`;
   - `applications/site-gateway-ci.yaml` and `ci/site-gateway/`.
2. **`site-gateway-os`.** Follow the decommission runbook's `virtual-machine` path, with the finalizer delete of the Application. After the cascade, clear the PAC Repository's `foregroundDeletion` finalizer, as that runbook describes.
3. **`site-gateway` CI.** Delete the `site-gateway-ci` Application with the resources finalizer. That removes, in `box1-ci`:
   - the PAC Repository `site-gateway` (clear its finalizer the same way);
   - the `site-gateway-release` ServiceAccount;
   - the `site-gateway-bundle` ImageStream;
   - the push Role and RoleBinding.
4. **Images and runs in `box1-ci`.** These are the last in-cluster references to the built images:

   ```bash
   oc -n box1-ci delete imagestream site-gateway-os site-gateway-os-disk site-gateway-bundle --ignore-not-found
   oc -n box1-ci delete pipelineruns -l pipelinesascode.tekton.dev/repository=site-gateway-os
   oc -n box1-ci delete pipelineruns -l pipelinesascode.tekton.dev/repository=site-gateway
   oc -n box1-ci delete pipelineruns -l backstage.io/kubernetes-id=site-gateway-os
   oc -n box1-ci delete pipelineruns -l backstage.io/kubernetes-id=site-gateway
   ```
5. **The status key.** Delete `box1-ci/vm-instance-status-ssh`. No image that trusts its public key is left after step 2.
6. **Hub state and catalog.**
   - Delete the `rhdh` ConfigMaps and Leases `box1-onboard-site-gateway` and `box1-onboard-site-gateway-os`.
   - Delete the two repository Locations (`https://github.com/box1-org/<repo>/tree/main/catalog-info.yaml`).
7. **Repositories.**
   - Close the open PRs in `site-gateway` and `site-gateway-os`.
   - Archive both repositories (`gh repo archive box1-org/<repo> --yes`), or delete them per the decommission runbook's step 4. Archiving is reversible; prefer it unless the owner asks for deletion.
8. **Verify.**
   - No `site-gateway*` Application, namespace, ImageStream or PAC Repository is left in the cluster.
   - The catalog lookups for both components return 404.

## Level 3: revert the golden-path changes

Do Levels 1 and 2 first. Plugin 1.2.0 has no `artifact` or `vm-instance` profile, so it cannot handle onboarding records of either kind. The reverted validator would also fail every `box1-workloads-dev` PR while a `vm-instance` workload or a `ci/` bundle exists.

1. **Roll the Hub back to plugin 1.2.0.**
   1. In one `box1-gitops` PR, set the pin in `platform/developer-hub/dynamic-plugins.yaml` back to `…box1-onboarding-plugin@sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b!box1-scaffolder-onboarding`.
   2. In the same PR, set the annotations in `platform/developer-hub/backstage.yaml` to that digest and to revision `8537ec131d6afc49bde020f6e110aa9073bdb0ac`.
   3. Merge it, check that no onboarding is running, and sync `developer-hub`.

   1.2.0 is already published, so nothing is rebuilt. The #136 characterisation test showed `service` and `virtual-machine` behave the same on 1.2.0 and on 1.5.x. Records of the remaining services and VMs, such as `agentic-operations` and `vm-golden-check`, carry no new profile, so 1.2.0 reads them unchanged.
2. **Revert `box1-templates`.** All its commits since the tag belong to the expansion, so one PR can restore the tag's tree:

   ```bash
   git checkout -b backout/site-expansion origin/main
   git revert --no-edit c074564 498afc3 d4e2364 1fc783b d73ee5d
   git diff pre-site-expansion-2026-11-09 --stat     # must be empty
   ```

   A dry run on 2026-11-10, against `main` `c074564`, applied all five reverts cleanly and left an empty diff from the tag. All five are single-parent commits, so `git revert` needs no `-m`.

   This removes the `quarkus-monorepo` and `vm-instance` templates and their Location entries, as well as `rhel-image-vm`'s `cloudInit` parameter. It also sets the plugin version back to 1.2.0.
   - **Don't tag a release.** The release pipeline refuses to re-release an existing version, and the Hub already runs the 1.2.0 digest from step 1.
   - **Check the catalog afterwards.** The template entities should be gone after the Location refreshes, so `template:default/quarkus-monorepo` and `template:default/vm-instance` return 404.
3. **Revert the expansion in `box1-gitops`.** In one PR, revert these commits, newest first, and **none of the unrelated ones**:

   | Commit | PR | Revert |
   |---|---|---|
   | `9689008` | #146 | yes, unless Level 1 already reverted it |
   | `8fe6189` | #143 | yes |
   | `3238ecf` | #141 | yes |
   | `ad18d69` | #140 | yes |
   | `01b2042` | #134 | yes |
   | `562929c` | #133 | yes |
   | `4bef9b0` | #132 | yes |

   ```bash
   git checkout -b backout/site-expansion origin/main
   git revert --no-edit 9689008 8fe6189 3238ecf ad18d69 01b2042 562929c 4bef9b0
   ```

   Leave out the plugin pins (#136, #147, #149): step 1 has already set the pin. Then check that only these paths differ from the tag:

   ```bash
   git diff pre-site-expansion-2026-11-09 --stat -- platform/pipelines platform/developer-hub/onboarding platform/identity/keycloak
   ```

   Only unrelated work may remain in that diff. A dry run on 2026-11-10, with the seven reverts on `main` `372545b`, left exactly these:

   | Path | Belongs to |
   |---|---|
   | `platform/pipelines/tasks/quarkus-maven.yaml` | builder image, #130 |
   | `platform/pipelines/tasks/security-gates.yaml` | builder image, #130 |
   | `platform/identity/keycloak/realm/openshift-client.yaml` | #131 |
   | `platform/identity/keycloak/realm/langfuse-client.yaml` | #142 |
   | two lines in `platform/identity/keycloak/realm/kustomization.yaml` | #131 and #142 |

   In that dry run, all seven reverts applied without conflicts.
4. **Sync and clean up.**
   1. Sync `pipelines-ci` and `developer-hub`. Neither syncs automatically, so sync with **prune** to remove the dropped Tasks and RBAC.
   2. Delete whatever the sync leaves behind:

      ```bash
      oc -n box1-ci get tasks.tekton.dev box1-maven-bundle box1-bundle-consumer-pr box1-bootc-status
      oc -n box1-ci get sa,secret ci-bundle-pull ci-bundle-pull-token
      ```
5. **Verify.**
   - `oc get tasks.tekton.dev box1-gitops-validate -n box1-ci -o yaml` no longer mentions `check_vm_instance`.
   - A `service` release still passes (for example the next `order-service` promotion).
   - A `virtual-machine` release still passes (`vm-golden-check` or `legacy-erp`).
   - The Hub runs digest `98506a25…`.
6. **Documentation and backlog.** Prompts, run state and achievement logs stay as history. Close #126 and #136–#141 with a link to the execution log below, or relabel them as deferred.

## Rolling forward again

Each back-out is a set of revert commits. Reverting those reverts restores the expansion. The `main` column in **The tags** records the forward state when this runbook was written.

- **Re-pinning the plugin.** Re-pin `sha256:209cbf816c…` (1.5.2) from box1-gitops#149.
- **Recreating the sites.** Recreating a site uses the `vm-instance` template and box1-docs#147's runbook.
- **Recreating `site-gateway-os`.** Recreating it from the template produces a new booted-digest key pair. Bake the new public key into the image, and recreate `vm-instance-status-ssh` with the private half.

## Execution log

No back-out has been run yet.
