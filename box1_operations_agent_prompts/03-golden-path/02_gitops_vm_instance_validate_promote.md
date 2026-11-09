# Golden path 02 — GitOps validate and promote for `vm-instance` workloads

> **Golden-path change, not a new service.** It changes the required GitOps check and the promotion task that every service and VM release goes through. Before starting, read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md` and `03_QUALITY_GATES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety rules:**
- `box1-gitops-validate` is a required check on every `box1-workloads-dev` PR, and `box1-gitops-promote` runs on every release. A bad change blocks all releases.
- Deliver changes only as reviewed `box1-gitops` PRs, and never with `oc apply`.
- The user merges. Wait about 10 seconds between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Put test materials and run state in `box1-docs`, not `box1-gitops`.
- Do not use Chrome.

**Issue:** [box1-docs#139](https://github.com/box1-org/box1-docs/issues/139), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies:**
- None to start.
- Coordinate the Secret and cloud-init rule with #140 (`03_vm_cloud_init_nocloud.md`). This run can go in parallel with #136 and #140.
- #138 (`05_vm_instance_profile_template.md`) depends on this run.
- #137 (`04_artifact_profile_quarkus_monorepo.md`) needs the `ci/` rule below.

## Mission

`gitops-validate` and `gitops-promote` must accept and correctly gate a new `vm-instance` workload profile: one bootc OS image repository, many VM instances, each in its own namespace and each pinning its own approved digest. They must also validate the `ci/` PaC-only directories that the `artifact` profile uses. Existing `service` and `virtual-machine` workloads must validate and promote unchanged.

## Verified baseline (observed 2026-11-08 on `box1-gitops` main `4bcc907`; verify before relying)

All paths below are in `box1-org/box1-gitops/platform/pipelines/tasks/` unless stated otherwise.

**`gitops-validate.yaml` (Task `box1-gitops-validate`)**
- The script is standard-library Python 3.11.
- `__main__` (L122–148) downloads the `box1-workloads-dev` zipball and pinned kubectl, then validates **only** `workloads/*/kustomization.yaml`.
- `profile_of()` (L59–64):
  - reads `box1.org/workload-profile` from the Namespace;
  - defaults to `service`;
  - asserts `profile in ['service','virtual-machine']` at L63.
- `validate()` (L116–120) returns the profile and dispatches with `check_vm if profile=='virtual-machine' else check_service` at L119.
- `check_vm` (L78–114):
  - exactly one VirtualMachine named after the workload (L87);
  - root volume `dataVolume: <name>-root` (L97);
  - serial disks `serviceca` and `regtoken` (L95–96);
  - with a zero digest: `Halted` and no DataVolume;
  - otherwise: one DataVolume `docker://…/box1-ci/<name>-disk@sha256:…` with `pullMethod: node` (L110–114).
  - **Secret rule (L98–104):** the service-account token Secret must carry no data, and every other Secret must be `stringData` holding only SSH public keys. A cloud-init userData Secret would fail. A `secretRef` to a Secret created outside Git would pass, because only rendered Secrets are checked.
- **Messages** use the style `assert cond, 'Sentence-case message'`, with no trailing period.

**`gitops-promote.yaml`**
- Params include:
  - `application-name` (default `quarkus-reference`);
  - `workload-profile` (default `service`);
  - `disk-digest`;
  - `environment` (`development` or `approval`).
- **`name` is overloaded.** It is the source repository (L89, `application='/repos/box1-org/'+name`), the workload directory, and the Argo Application. The superseded-revision checks at L266 and L316 require `box1-org/<name>` main to equal `revision`.
- `candidate_paths()` (L96) and `plan_updates()` (L102–138):
  - **service:** updates the kustomization digest and the deployment annotations.
  - **virtual-machine:** every promotion updates the `os-image-digest`, `source-revision` and `build-pipelinerun` annotations. The first promotion also changes `Halted` to `Always`, swaps the DataVolume zero digest, and inserts `datavolume.yaml` into the kustomization.
- **Required checks:** `development` waits for `box1-phase1-smoke-` and `box1-gitops-validate-` (L292). Required checks are enforced by this task and by the plugin (`box1-templates/.../workflow.cjs:401`), **not** by GitHub branch protection (`AUTOMATION.md:77-79`).

**Other tasks**
- `bootc-channel.yaml` copies `box1-ci/<image-name>@digest` to the tag `:<channel>`. There is one tag per image per channel.
- `bootc-disk.yaml` records `box1-ci/<image-name>:<channel>` as the guest's update source.
- `vm-smoke.yaml` (L57–58) and `bootc-apply.yaml` (L87, L111) use `application-name` as both the Argo Application name and the VM name.

**Tests**
- `test-gitops-validate.py`:
  - extracts the script from the YAML;
  - `vm_bundle()` fixtures are at L41–151;
  - `VirtualMachineProfile` has 14 cases.
  - `ServiceProfileRegression` (L260–269) runs only with `BOX1_WORKLOADS_DEV` set and asserts that **every** workload returns `service`. That **probably fails today**, because `legacy-erp` and `vm-golden-check` return `virtual-machine`. This is inferred and not run.
- `test-gitops-promote.py`:
  - extracts the pure helpers;
  - covers `PromotionPlan` service and VM cases.
- **Neither file runs in any CI pipeline.** They are manual commands in `platform/pipelines/GOLDEN-PATH.md:170-173`.

**`box1-workloads-dev`**
- `applications/<name>.yaml` defines one Application per workload. There is no ApplicationSet. The parent Application is `box1-gitops/applications/workloads-dev.yaml`.
- The VM workload shapes are in `workloads/vm-golden-check/` and `workloads/legacy-erp/`.
- `.tekton/validate-quarkus-gitops.yaml` runs the validator.

## Decided design

The owner decided the channel and PaC-location questions on 2026-11-08. They are recorded on #139 and #137.

### Profile dispatch

- In `gitops-validate`, replace the `if/else` dispatch with a profile table. Accepted profiles become `service`, `virtual-machine` and `vm-instance`.

### `check_vm_instance` rules

- The Namespace carries `box1.org/workload-profile: vm-instance`.
- Exactly one VirtualMachine exists, named after the instance (the workload directory name).
- The VM carries an annotation (proposed `box1.org/source-image: <source-repo>`) naming the source OS image repository. That source must appear in an **allowlist** kept in `box1-gitops`, for example a `vm-instance-sources` list inside the validator Task or a ConfigMap the task reads. Record which.
- **Disk rules:**
  - With a non-zero digest: one DataVolume `<instance>-root` from `docker://…/box1-ci/<source>-disk@sha256:<digest>`. It must not be the zero digest or a tag, and must use `pullMethod: node`.
  - With a zero or absent digest: `Halted`.
  - The `serviceca` and `regtoken` serial disks follow the VM golden-path rules.
- **cloud-init (with #140):**
  - Require a `cloudInitNoCloud` volume that uses `secretRef` (proposed name `<instance>-cloud-init`).
  - **Forbid** inline `userData`, `userDataBase64`, `networkData` and `networkDataBase64`.
  - The referenced Secret must **not** be rendered from Git.
  - A non-secret `<instance>-site` ConfigMap is allowed, and is checked for credential-looking keys (`secret`, `password`, `token`, `key` values).
  - The Secret rule from `check_vm` otherwise applies unchanged.
- **Failure messages:** mismatched VM name, an unpinned or tag disk, a source outside the allowlist, and an inline secret or userData must each fail with a readable sentence.

### `ci/` rule for #137 (`artifact` profile)

- The owner chose `box1-workloads-dev/ci/<repo>/` for the PaC Repository of code-only repositories, plus `applications/<repo>-ci.yaml` targeting `box1-ci`.
- **Validation:** `__main__` also validates `ci/*/kustomization.yaml`. A `ci/` bundle may hold only the PaC `Repository` and the observer and image-push Roles and RoleBindings that #137 needs, all in `box1-ci`. It may not hold workloads, Secrets with data, or namespaces.
- Agree the exact resource list with the #137 run, or define it here and have #137 consume it.

### `gitops-promote`

- Add a `vm-instance` target, with a new param (proposed `instance-name`, default empty) separate from `application-name`.
- **Repo checks:** the superseded-revision checks use the **source** repository (`application-name`).
- **Files edited:** only `workloads/<instance>/virtualmachine.yaml` and `datavolume.yaml` are edited, along with `kustomization.yaml` on first promotion.
- **Argo sync:** the sync targets the `<instance>` Application.
- **Disk-digest swap:** a day-2 instance promotion also swaps the DataVolume digest, because there is no channel to follow.
- Keep the existing `service` and `virtual-machine` code paths byte-for-byte identical.

### Channels (owner decision)

- `vm-instance` workloads **pin digests only**.
- `bootc-channel` keeps moving the source image's shared `:<channel>` tag, and instances never auto-upgrade from it. Day-2 per-instance upgrades are #141's concern; flag any requirement this places on `bootc-disk`'s recorded update source.
- **Not taken:** a per-instance channel tag.

### Test-suite fix

- Fix `ServiceProfileRegression` so it asserts the profile each workload declares, not `service` for all. Run it against a current `box1-workloads-dev` checkout.
- Propose wiring both Python suites into an existing `box1-gitops` PR pipeline. If that is out of scope, file a backlog issue and link it.

## Scope and guardrails

**In scope**
- `gitops-validate.yaml`, `gitops-promote.yaml` and their two test files.
- The allowlist.
- The `box1-workloads-dev/.tekton/` runner, only if the validator's inputs change.
- Documentation in `platform/pipelines/GOLDEN-PATH.md`.

**Out of scope**
- `bootc-*`, `vm-smoke` and `bootc-apply`, except to document what #138 and #141 need from them.
- Templates and the plugin. Those belong to #136, #137, #138 and #140.

**Rules**
- Add test cases **before** changing behaviour. Every existing test must keep passing unchanged.
- When the validator Task changes, the box1-workloads-dev required check uses the new Task as soon as Argo syncs it. Sequence the merge so no open `box1-workloads-dev` PR is left failing, and say so in the PR body.

## Verifiable acceptance evidence

These items come from the issue. Tick each on #139 only with the named evidence.

- [ ] A valid `vm-instance` bundle passes the required `box1-gitops-validate` check. A bundle with a mismatched VM name, an unpinned disk, or an inline secret fails with a readable reason.
  - *Evidence:* the new test cases and their output, plus one real `box1-gitops-validate` PipelineRun on a draft `box1-workloads-dev` PR that carries a `vm-instance` fixture. Close the PR without merging, and record that.
- [ ] A promotion PR for one instance changes only that instance's files.
  - *Evidence:* a `PromotionPlan` test that has two instances of one source and asserts the changed paths. A live promotion is #138's acceptance.
- [ ] Existing `service` and `virtual-machine` workloads validate and promote unchanged (test cases in `test-gitops-promote.py` and the validator tests).
  - *Evidence:* the full output of both suites, `ServiceProfileRegression` fixed and run with `BOX1_WORKLOADS_DEV` set, and the first real service and VM releases after the merge passing their required checks.

## Frontier profile

Use this with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/139-gitops-vm-instance/`.

**Discovery must cover:**
- current `main` of `box1-gitops` and `box1-workloads-dev`;
- every caller of `box1-gitops-promote` and `workload-profile` (templates, `legacy-erp`'s appliance pipeline, the plugin);
- the KubeVirt `cloudInitNoCloud.secretRef` field on the installed OpenShift Virtualization version, so the CRD must be inspected, not assumed;
- the current result of running both test suites, before any change.

**Design decisions to record:**
- the allowlist location and format;
- the source annotation name;
- the instance param name;
- the `ci/` resource list, agreed with #137;
- whether the Python suites join CI.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Baseline test results recorded, including whether `ServiceProfileRegression` fails |
| 3 Implementation | New cases added first; all old cases unchanged and passing |
| 6 Delivery | `box1-gitops` PR merged by the user; Argo shows the new Task revision |
| 7 Live acceptance | Real validate run on a `vm-instance` fixture, and real service and VM releases after the merge passing |

**Verification scenarios:**
- valid instance, Halted and promoted;
- wrong VM name;
- disk from a tag, or from another source not on the allowlist;
- zero digest while `Always`;
- inline `userData`;
- a Secret with data in Git;
- a credential key in the site ConfigMap;
- two instances of one source, promoting one;
- the `service` and `virtual-machine` regressions;
- a `ci/` bundle carrying a Deployment, which must be rejected.

**Stop conditions:**
- the installed KubeVirt rejects `cloudInitNoCloud.secretRef`;
- a change that would alter the outcome of an existing workload's validation;
- an open `box1-workloads-dev` PR the new rule would fail.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the rules added and their exact messages;
- the allowlist location;
- the promote param contract for #138, with an example `taskRef` params block;
- the `ci/` contract for #137;
- the test outputs;
- the merged PR and Argo revision;
- the rollback, which is a revert PR of the Task change.

Tick the completed items on #139.
