# Site Expansion golden path: artifact and vm-instance profiles, cloud-init, GitOps rules

**Date:** 2026-11-08 to 2026-11-09 (America/New_York). Prompts written about 21:00–23:00 EST on 11-08; implemented overnight; released 00:40–00:55 EST on 11-09; corrected during 21:45–23:55 EST on 11-09.

**Status:** Released and in use. These are the golden-path prerequisites ([#136](https://github.com/box1-org/box1-docs/issues/136)–[#140](https://github.com/box1-org/box1-docs/issues/140)) of the Site Expansion epic [#126](https://github.com/box1-org/box1-docs/issues/126). All five issues stay open for their remaining live criteria, which are listed under **Follow-ups**.

**Builds on:**
- the [RHEL image mode VM golden path](2026-11-05-rhdh-vm-golden-path.md) (plugin 1.2.0);
- the [phased onboarding plugin](2026-11-04-rhdh-onboarding-refactor.md) and its [OCI delivery](2026-11-05-rhdh-onboarding-plugin-oci.md).

The first use of these paths, the edge sites, is recorded in [2026-11-10 edge sites onboarded](2026-11-10-edge-sites-onboarded.md).

## Outcome

Developer Hub has two new golden paths beside the Quarkus service and RHEL VM paths:

- **Create Quarkus Multi-Module Repository** (`quarkus-monorepo`, `artifact` profile). It creates a code-only repository and deploys nothing:
  - PRs run a multi-module `mvn verify`;
  - a merge to `main` publishes a deterministic `FROM scratch` bundle by digest to `box1-ci/<repo>-bundle`, with the JARs inside;
  - the bundle passes the security gate in `gate` mode;
  - the release then opens a digest-bump PR in a declared consumer repository.
- **Add a VM Instance (Site) of an OS Image** (`vm-instance` profile). It adds one more VM of an already built and approved bootc image, with no repository and no build. The VM gets:
  - its own namespace;
  - its own approved digest, pinned in GitOps;
  - its own identity, delivered through cloud-init (NoCloud) with the secret passed by reference only;
  - a booted-digest check through a restricted guest user.

The onboarding plugin is now a profile dispatch table. A new profile is a table entry plus its handlers. `service` and `virtual-machine` behave byte-for-byte as in 1.2.0. The Hub runs **plugin 1.5.2** (`sha256:209cbf816c…`).

## Starting baseline

- **Plugin 1.2.0** (`sha256:98506a25…`): a two-way `this.vm` switch, tested in 10 places in `workflow.cjs`. Every phase assumed a deployed workload, and one VM repository produced exactly one VM named after it.
- **Validator:** `box1-gitops-validate` accepted only `service` and `virtual-machine`, required exactly one VM named after the workload, and rejected any Secret except SSH public keys.
- **Promotion:** `box1-gitops-promote` used one name for the source repository, the workload directory and the Application.
- **No cloud-init:** nothing in Box1 used cloud-init. Guests received only SSH keys (through the guest agent), the service CA and a registry token (both as serial disks).
- **Tests:** the Python contract tests ran in no CI. `ServiceProfileRegression` failed against the live workloads repo (2 failures, `legacy-erp` and `vm-golden-check`), and nobody had noticed.
- **Precedent:** the earlier `box1-ops-erp-simulator` → `legacy-erp` scratch bundle, which #137 named as its model, was no longer produced.

## What changed

**Prompts:**
- [box1-docs#143](https://github.com/box1-org/box1-docs/pull/143) added the five frontier prompts in `box1_operations_agent_prompts/03-golden-path/` (manifest 1.9).
- The owner's decisions are recorded on the issues:
  - instances pin digests only;
  - `artifact` PaC Repositories go in `box1-workloads-dev/ci/<repo>/`;
  - the cloud-init Secret is assembled outside Git from a non-secret site ConfigMap.

**Implementation.** Each issue ran as a frontier agent run, with run state in `agent-runs/13x-*` ([#145](https://github.com/box1-org/box1-docs/pull/145), [#146](https://github.com/box1-org/box1-docs/pull/146), [#147](https://github.com/box1-org/box1-docs/pull/147), [#148](https://github.com/box1-org/box1-docs/pull/148), [#150](https://github.com/box1-org/box1-docs/pull/150)).

| Repository | PRs | Change |
|---|---|---|
| box1-templates | [#33](https://github.com/box1-org/box1-templates/pull/33) | Plugin dispatch table (1.3.0). Characterisation test committed before the refactor and unchanged after it |
| box1-templates | [#34](https://github.com/box1-org/box1-templates/pull/34) | `rhel-image-vm` gets an optional `cloudInit` parameter (template 1.1.0). With it off, the render is byte-identical to before |
| box1-templates | [#35](https://github.com/box1-org/box1-templates/pull/35), [#36](https://github.com/box1-org/box1-templates/pull/36), landed on `main` by [#37](https://github.com/box1-org/box1-templates/pull/37) | `quarkus-monorepo` template and `artifact` profile (1.4.0). `vm-instance` template and profile (1.5.0) |
| box1-gitops | [#132](https://github.com/box1-org/box1-gitops/pull/132) | Validator: `vm-instance` and `ci/` rules, plus the `ServiceProfileRegression` fix. Promotion: `instance-name` target |
| box1-gitops | [#133](https://github.com/box1-org/box1-gitops/pull/133) | `box1-maven-bundle` and `box1-bundle-consumer-pr` Tasks. `box1-quarkus-maven` is unchanged and pinned by hash |
| box1-gitops | [#134](https://github.com/box1-org/box1-gitops/pull/134) | #140's rules reconciled into the validator; `box1-bootc-status` Task; Hub read access to `imagestreamimages` |
| box1-gitops | [#136](https://github.com/box1-org/box1-gitops/pull/136) | Pin plugin 1.5.0 (`sha256:f2dd0e1e…`, release `box1-onboarding-plugin-release-zqtwq`) |

**Stacked PRs that missed `main`.** Templates #35 and #36 were stacked PRs. They merged into their parent branches, because box1-templates did not delete merged branches, so the new templates never reached `main` or the Hub. [#37](https://github.com/box1-org/box1-templates/pull/37) replayed their four commits onto `main` (all tests passing), and 1.5.0 was released from that merge.

**Fixes found in live use**

| Repository | PR | Problem | Fix |
|---|---|---|---|
| box1-gitops | [#140](https://github.com/box1-org/box1-gitops/pull/140) | A consumer's `COPY --from=…svc:5000/box1-ci/<repo>-bundle@sha256:…` failed: the build had no registry credentials and no CA for the service host | `box1-bootc-build` logs in to `registry.apps.ocp.box1.org` with its ServiceAccount token |
| box1-gitops | [#141](https://github.com/box1-org/box1-gitops/pull/141) | #140 broke every bootc PR check: `ci-bootc-check` has no token by design | Log in only when a token is mounted. PR builds pull as a new account, `box1-ci/ci-bundle-pull` (no Role, no SCC, never pushes) |
| box1-gitops | [#143](https://github.com/box1-org/box1-gitops/pull/143) | A pull-only `<repo>-bundle-pull` Role and its validator exception were added on the belief that build accounts could not pull from `box1-ci`. That came from a malformed `oc auth can-i get imagestreams/layers` query | Exception and docs removed. Every ServiceAccount in `box1-ci` already pulls through `system:image-pullers`. The Role itself was reverted in [box1-workloads-dev#209](https://github.com/box1-org/box1-workloads-dev/pull/209), and the template change was closed unmerged ([box1-templates#38](https://github.com/box1-org/box1-templates/pull/38)) |
| box1-templates | [#39](https://github.com/box1-org/box1-templates/pull/39) (1.5.1, `sha256:6e8a0508…`) | The `vm-instance` catalog check compared `managed-by-location` with a `blob/` URL, but Backstage stores it in `tree/` form, so every existing instance entity failed | Register `tree/`, and compare normalised URLs |
| box1-templates | [#40](https://github.com/box1-org/box1-templates/pull/40) (1.5.2, `sha256:209cbf81…`) | Reusing a decommissioned name adopted the earlier onboarding's merged PR, found by branch name; `merge()` skipped verification for merged PRs | A PR counts only if its body carries this onboarding's id; `merge()` checks the id too |

The pins for 1.5.1 and 1.5.2 are [box1-gitops#147](https://github.com/box1-org/box1-gitops/pull/147) and [#149](https://github.com/box1-org/box1-gitops/pull/149). In each fix the test was updated first and shown to fail on the old code, including the 1.5.1 catalog fixture, which now records locations the way Backstage does.

## Validation and evidence

**Tests (local and CI):**

| Repository | Tests | Result |
|---|---|---|
| box1-templates | `npm run validate` | pass |
| box1-templates | `test:onboarding` (plugin) | 109/109 at 1.5.2 |
| box1-templates | `test:onboarding-oci` | pass |
| box1-gitops | `test-gitops-validate.py` | 96 |
| box1-gitops | `test-gitops-promote.py` | 31 |
| box1-gitops | `test-maven-bundle.py` | 26 |

**Live:**
- **Releases:** each plugin version was released by tag and pinned through the release pipeline's PR. Each time the Hub logged the new digest installed and `box1-scaffolder-onboarding-dynamic` loaded; at 1.5.0 that included the new action `box1:development:resolve-source`.
- **Templates:** the catalog lists `template:default/quarkus-monorepo` and `template:default/vm-instance`.
- **First real use:** `site-gateway`, `site-gateway-os`, `site-west` and `site-east` were created and verified through these paths; see the [edge sites log](2026-11-10-edge-sites-onboarded.md).
- **Validator in production:** after `pipelines-ci` synced, these passed `box1-gitops-validate` and promoted:
  - `agentic-operations`, a service ([box1-workloads-dev#212](https://github.com/box1-org/box1-workloads-dev/pull/212));
  - `site-gateway-os`, a VM ([#208](https://github.com/box1-org/box1-workloads-dev/pull/208), [#213](https://github.com/box1-org/box1-workloads-dev/pull/213), [#219](https://github.com/box1-org/box1-workloads-dev/pull/219)).

**Acceptance items ticked with this evidence:**

| Issue | Ticked | Total |
|---|---|---|
| #136 | 3 | 4 |
| #137 | 3 | 5 |
| #138 | 2 | 4 |
| #139 | 2 | 3 |
| #140 | 3 | 4 |

Details are in each issue's 2026-11-10 evidence comment.

## Final operational state

| Component | State | Managed by |
|---|---|---|
| Onboarding plugin | 1.5.2, `sha256:209cbf816c…`, revision `c074564` | `box1-gitops` `platform/developer-hub/dynamic-plugins.yaml`, synced to `developer-hub` |
| Templates | `quarkus-rest-service`, `github-repository`, `rhel-image-vm` (with `cloudInit`), `quarkus-monorepo`, `vm-instance` | `box1-templates` root Location |
| CI Tasks and validator | `box1-gitops` `main` `8fe6189` and later, synced to `pipelines-ci` (manual sync) | `box1-gitops` |
| `box1-ci/ci-bundle-pull` and its token Secret | Present; token filled by the token controller | `box1-gitops` `platform/pipelines/ci/bootc-build.yaml` |

**Deliberate limits:**
- Day-2 promotion of an instance updates only its annotations. The DataVolume is not swapped, because CDI treats DataVolume specs as immutable. Upgrading the OS in place on an instance is #141's job.
- An instance's onboarding record pins the digest it adopted. Moving an instance to a new image currently means recreating it.

## Recovery and follow-ups

**Back-out:**
- The annotated tags `pre-site-expansion-2026-11-09` mark the state before this work.
- The three-level procedure is [runbooks/site-expansion-backout.md](../../runbooks/site-expansion-backout.md). Its Git revert sets were dry-run cleanly; the cluster steps have not been run.

**Rollback of the plugin alone:** re-pin `sha256:98506a25…` (1.2.0) through `box1-gitops`, then sync `developer-hub`. `service` and `virtual-machine` behave identically. Records of the new profiles would have to be removed first.

**Open:**
- #136: a recorded live verify of a Quarkus service regression.
- #137: a policy-failure bundle is not proposed; the Quarkus service regression.
- #138: promoting one instance alone; a decommission while another instance exists.
- #139: the negative validator cases in a real check run.
- #140: re-creating a VM with a data disk kept.
- [#151](https://github.com/box1-org/box1-docs/issues/151): run the GitOps Python suites in CI.
- [#157](https://github.com/box1-org/box1-docs/issues/157): plugin retries on transient GitHub and Kubernetes errors.
- [#141](https://github.com/box1-org/box1-docs/issues/141): staged per-site OS rollout.
