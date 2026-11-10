# D-004 `ci/<repo>/` resource list (contract for #137)

**Defined here for #137 to consume.** It was not negotiated with a live #137 run; none was active.

**Allowed kinds (with exact apiVersion), all in namespace `box1-ci`:**
- `Repository` (`pipelinesascode.tekton.dev/v1alpha1`)
- `ServiceAccount` (`v1`)
- `ImageStream` (`image.openshift.io/v1`)
- `Role` and `RoleBinding` (`rbac.authorization.k8s.io/v1`)

**Names:**
- Exactly one Repository, named `<repo>`.
- ImageStream: `<repo>-bundle`.
- Everything else: `<repo>-<purpose>`. Suggested names: `<repo>-release`, `<repo>-bundle-push`, `<repo>-release-observer`.

**Repository:**
- `spec` keys ⊆ {url, concurrency_limit, settings}.
- `settings` keys ⊆ {pipelinerun_provenance, github_app_token_scope_repos}.
- `url` is `https://github.com/box1-org/<repo>`.
- `pipelinerun_provenance: default_branch`.
- Token scope: `box1-org/<name>` only, never `box1-gitops` or `box1-workloads-dev`.

**Roles:**
- Every rule has `resourceNames`.
- No `*` anywhere.
- No `secrets`.
- No `exec`, `attach`, `portforward`, `proxy` or `token` subresources.
- Verbs are `get`, `list` or `watch`. A rule on exactly `imagestreams/layers` with resourceNames exactly `[<repo>-bundle]` may also `update` (push).

**RoleBindings:** `roleRef` is a Role in the same bundle. Subjects are ServiceAccounts in `box1-ci` that are declared in the bundle, or `ci-observe`.

**Collisions:** a `ci/<repo>` must not share a name with `workloads/<repo>`.

**Deviation from the #139 prompt's wording** ("only the PaC Repository and the observer and image-push Roles and RoleBindings"): ServiceAccount and ImageStream are added.
- #137's prompt (line 104) needs the release ServiceAccount.
- A push Role scoped by `resourceNames` needs the ImageStream to exist, as in `box1-gitops/platform/pipelines/ci/box1-ops-erp-simulator.yaml`.

Secrets are rejected outright, not only "Secrets with data". Anything #137 needs outside `box1-ci` (cluster RBAC, an Argo observer in `openshift-gitops`) goes in box1-gitops.

**Not validated:** `applications/<repo>-ci.yaml`. The validator does not read `applications/`.
