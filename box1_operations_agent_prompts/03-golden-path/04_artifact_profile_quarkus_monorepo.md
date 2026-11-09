# Golden path 04 — `artifact` profile and `quarkus-monorepo` template

> **This is a golden-path change, not a new service.** It adds a code-only golden path: a multi-module Quarkus repository that publishes an OCI bundle by digest and deploys nothing. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md` and `03_QUALITY_GATES.md` first. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety rules:**
- The existing `quarkus-rest-service` and `rhel-image-vm` paths must not change behaviour.
- Creating repositories, running onboarding, and merging to `main` or GitOps all need approval.
- The user merges. Wait about 10 s between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Put test materials in `box1-docs`, not `box1-gitops`.
- Do not use Chrome.

**Issue:** [box1-docs#137](https://github.com/box1-org/box1-docs/issues/137), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies:**
- [#136](https://github.com/box1-org/box1-docs/issues/136) (`01_onboarding_profile_dispatch.md`) must be released first, because this run adds a profile to its table.
- The `ci/` validation rule comes from [#139](https://github.com/box1-org/box1-docs/issues/139) (`02_gitops_vm_instance_validate_promote.md`). Agree it with that run, or implement it there.
- The consumer repository, `site-gateway-os`, is created in #126 from `rhel-image-vm`. Until it exists, prove the consumer PR against a throwaway consumer (approval required) or stop at that criterion.

## Mission

Ship a `quarkus-monorepo` Developer Hub template and an `artifact` onboarding profile. A repository created from them must:
- run multi-module `mvn verify` on PRs as a required check;
- on merge to `main`, package the module JARs into a `FROM scratch` OCI bundle;
- push the bundle by digest to `box1-ci/<repo>-bundle`;
- gate the bundle with `box1-security-gates`;
- open a digest-bump PR in a declared consumer repository.

There must be no namespace, Deployment, Route or Argo workload Application. The first user is `site-gateway`, with modules `gateway`, `ops` and `simulator`, consumed by `site-gateway-os`.

## Verified baseline (observed 2026-11-08; verify before relying)

**The precedent cited in the issue no longer runs.**
- The `box1-ops-erp-simulator` → `legacy-erp` scratch bundle is no longer produced.
  - `legacy-erp` now builds the simulator from source in a multistage Containerfile, through `box1-bootc-build`'s `extra-source-*` params.
  - `box1-gitops/platform/pipelines/ci/box1-ops-erp-simulator.yaml:10-11` says so.
  - That file still holds the `ci-erp-release` SA, the ImageStream and a push Role scoped to one ImageStream, all now unused.
- Two reusable pieces remain:
  - `box1-ops-erp-simulator/scripts/make-oci-layout.py` (on `main`). It is standard-library only and deterministic, refuses symlinks, and uses fixed timestamps.
  - The old pipeline at `box1-ops-erp-simulator` commit `193ba707c636`, `.tekton/release.yaml`. It builds a reproducible artifact, runs `make-oci-layout.py`, does an **unprivileged** `skopeo copy … --digestfile` push to `box1-ci/<name>:<revision>`, then runs `box1-security-gates`.
  - The consumer pattern is documented as `COPY --from=…/box1-ci/<bundle>@sha256:<digest> / <path>` (`achv-assistant/agent-runs/14-erp-appliance/decisions/D-002-ci-and-artifact.md`). No current Containerfile uses it.

**Maven build task**
- `box1-gitops/platform/pipelines/tasks/quarkus-maven.yaml` runs `mvn verify` (L92), then a Jib push.
- It reads `target/jib-image.digest` **at the repository root** (L106–108). A multi-module build has no such file.
- Its builder image is `box1-builder@sha256:358c…`.

**Security gates**
- `box1-gitops/platform/pipelines/tasks/security-gates.yaml` requires `image-reference` to end in `@sha256:`.
- `enforcement` is one of `disabled`, `observe` or `gate`.
- It runs syft → RHTPA, then roxctl.

**Service template**
- `templates/quarkus-rest-service` (template version 1.2.0) is single-module, with `<packaging>quarkus</packaging>`.
- `.tekton/pull-request.yaml` runs as `ci-test`, through `box1-quarkus-maven` with `push-image:'false'`.
- `.tekton/release.yaml` runs as `ci-build`. It chains maven → security (`gate`) → `box1-gitops-promote` → smoke, with `taskRunSpecs` (promote as `ci-gitops`, smoke as `ci-observe`).

**Template registration**
- `box1-templates/catalog-info.yaml` is a `Location` that lists each template.
- `scripts/validate.mjs` L162/L208 checks that list and renders each template.

**PaC Repositories**
- Hand-onboarded repos are declared in `box1-gitops/platform/pipelines/ci/*.yaml`. They use `concurrency_limit: 1`, `pipelinerun_provenance: default_branch` and `github_app_token_scope_repos`.
- Onboarded workloads declare theirs in `box1-workloads-dev/workloads/<name>/onboarding.yaml`.
- `gitops-validate` today validates only `workloads/*`.

**Onboarding plugin**
- Every phase today expects a deployed workload (see the #136 prompt).
- `registerCatalog` requires `deploymentImage`.

## Decided design

The owner decided this on 2026-11-08. The PaC-location decision is recorded on #137.

### Template: `templates/quarkus-monorepo`

- **Parameters:** `name`, `description`, `owner`, `visibility`, the module list (default `gateway, ops, simulator`) and the consumer repository plus path (for `site-gateway`: `site-gateway-os`, `Containerfile`).
- **Skeleton:**
  - a parent `pom.xml` (`<packaging>pom</packaging>`, Java 21, Quarkus 3 BOM matching `quarkus-reference`) with one module per entry;
  - minimal tests in each module;
  - `README.md` and `docs/`;
  - `catalog-info.yaml`: a Component with a non-service type such as `library`, the project slug, `techdocs-ref` and `janus-idp.io/tekton`, but **no** `backstage.io/kubernetes-id` and no `argocd/*` annotations;
  - `.tekton/pull-request.yaml` and `.tekton/release.yaml`.
- **Profile:** every onboarding step passes `profile: artifact`.

### Build

- Add a new cluster Task (proposed `box1-maven-bundle`), or a bundle step after `box1-quarkus-maven` with `push-image:'false'`. Pick whichever keeps `box1-quarkus-maven` byte-identical for services, and record the choice.
- The step packages each module's runnable output (Quarkus `quarkus-app/` fast-jar directories) under fixed paths, for example `/<module>/quarkus-app/`.
- It builds a deterministic one-layer `FROM scratch` OCI layout (reuse `make-oci-layout.py` or an equivalent).
- It pushes unprivileged with `skopeo copy --digestfile` to `registry.apps.ocp.box1.org/box1-ci/<repo>-bundle:<revision>` and returns `image-digest`.

### Release pipeline

1. build and bundle;
2. `box1-security-gates` (`enforcement: gate`, `image-reference …/box1-ci/<repo>-bundle@<digest>`);
3. **consumer PR**, only when the gate passes. It opens a PR in the declared consumer repository that rewrites the single `COPY --from=…/box1-ci/<repo>-bundle@sha256:…` line. It never merges the PR.

A bundle that fails policy is never proposed.

### No GitOps workload; PaC in `box1-workloads-dev/ci/<repo>/` (owner decision)

- The onboarding PR adds `ci/<repo>/` holding:
  - the PaC `Repository` in `box1-ci`, with `github_app_token_scope_repos` including the consumer;
  - the release ServiceAccount, the push Role and RoleBinding for ImageStream `<repo>-bundle`, and the observer Roles.
- It also adds `applications/<repo>-ci.yaml`, targeting `box1-ci`.
- The plugin keeps its existing PR, required-check and merge path in `box1-workloads-dev`.
- Not taken: `box1-gitops/platform/pipelines/ci/`. That would need a new plugin write path into the platform repo.

### `artifact` profile handlers (in the #136 table)

- **Bundle validation:** accepts only the `ci/` files and the Application.
- **Provision:** skipped, or limited to the `ci/` Application sync.
- **Build barrier and platform checks:** the release ServiceAccount and push binding exist, and the PaC Repository is ready. No namespace or Deployment checks.
- **Build:** a PipelineRun of the bundle task. It returns `image-digest`.
- **Promote:** there is no workload promotion. Record the consumer PR URL from the release, or open it.
- **Verify:**
  - the bundle digest exists in `box1-ci/<repo>-bundle`;
  - the gate result is recorded;
  - the consumer PR exists or has merged.
- **Catalog:** the completion predicate uses the bundle digest instead of `deploymentImage`.

### Reposilite

Reposilite remains a dependency cache only. No JARs are published to it.

## Scope and guardrails

**In scope:**
- `box1-templates`: the new template, the `artifact` profile entry and handlers in the plugin, `catalog-info.yaml`, `scripts/validate.mjs` and tests;
- `box1-gitops`: the bundle Task, plus cluster RBAC that cannot live in `ci/<repo>/`;
- `box1-workloads-dev`: `ci/` only, through onboarding.

**Out of scope:**
- `site-gateway`'s real application code (#127 onward);
- `site-gateway-os` itself (#126);
- changes to `box1-quarkus-maven`'s behaviour for services.

**Release:** the plugin release follows the #136 process with a new version, followed by the pin PR and a Hub sync. The Hub sync has standing approval once you have checked that no onboarding is active.

## Verifiable acceptance evidence

These criteria come from the issue. Tick each on #137 only with the named evidence.

- [ ] Creating `site-gateway` from Developer Hub produces the repo, catalog entry and pipelines, with no namespace, Deployment or Argo Application.
  - *Evidence:* the Hub task ID, the repository tree, the catalog entity, the `ci/site-gateway` Application, and `oc get ns site-gateway-dev` returning NotFound.
  - Onboarding needs approval. The Argo Application in question is the *workload* Application; the `ci/` Application is expected.
- [ ] A PR runs the multi-module `mvn verify` and reports a required check.
  - *Evidence:* the PR's check run and its log showing every module tested.
- [ ] A merge to `main` publishes a bundle by digest, passes the security gate in `gate` mode, and opens a digest-bump PR in `site-gateway-os`.
  - *Evidence:* the release PipelineRun results, `skopeo inspect` of the digest showing its layer contents, the gate output, and the consumer PR diff (one line).
- [ ] A bundle that fails policy is not proposed to the consumer.
  - *Evidence:* a deliberate policy failure in a throwaway repository or branch (approval required), the gate failing, and no consumer PR opened.
- [ ] The `quarkus-rest-service` and `rhel-image-vm` templates still pass their regression onboarding.
  - *Evidence:* both regression runs on the new plugin digest, then decommissioned.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/137-artifact-profile/`.

**Discovery must cover:**
- the released #136 handler interface and digest;
- the #139 `ci/` rule's status;
- whether `site-gateway` and `site-gateway-os` exist yet;
- the GitHub App's installation scope (can it open PRs in the consumer?);
- the registry ImageStream naming and push RBAC in `box1-ci`;
- the `box1-builder` image contents (Maven, skopeo availability).

**Design decisions to record:**
- whether the bundle is a new Task or a step;
- the bundle layout inside the image, agreed with the `site-gateway-os` Containerfile;
- how the consumer is declared (template parameter stored where);
- the catalog Component type;
- the `ci/` resource list;
- the plugin version.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | #136 released; consumer availability known |
| 3 Implementation | Template renders and validates in `npm run validate`; service and VM renders unchanged |
| 6 Delivery | Plugin digest pinned; bundle Task merged in `box1-gitops`; Hub synced |
| 7 Live acceptance | All five criteria with evidence |

**Verification scenarios:**
- one module fails its tests (no publish);
- a gate failure (no consumer PR);
- a consumer file with zero or two `COPY --from` bundle lines (fails clearly);
- the consumer PR already open for an older digest (updated or superseded, not duplicated);
- a rerun of the same revision (same digest, idempotent PR);
- the service and VM regression runs.

**Stop conditions:**
- #136 is not released;
- the GitHub App cannot reach the consumer;
- `site-gateway-os` does not exist and no throwaway consumer is approved;
- a change would alter `box1-quarkus-maven` for services.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the template path and version;
- the profile handlers;
- the bundle Task;
- the `ci/` contract;
- the bundle digest and gate result;
- the consumer PR;
- the regression task IDs;
- the rollback: the previous plugin digest from the pin PR, then reverting the template from the Location.

Tick the completed items on #137.
