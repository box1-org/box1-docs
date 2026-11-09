# Golden path 01 — Onboarding plugin profile dispatch table

> **Golden-path change, not a new service.** It changes the Developer Hub onboarding plugin that every existing service and VM depends on. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md` and `03_QUALITY_GATES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety:** this plugin onboards every Box1 service and VM. A regression breaks the golden path for all of them. Release only through the existing tag pipeline, and never re-release an existing version. Merges belong to the user. Wait about 10 seconds between merges ([#64](https://github.com/box1-org/box1-docs/issues/64)). Do not use Chrome or its extension.

**Issue:** [box1-docs#136](https://github.com/box1-org/box1-docs/issues/136), a sub-issue of the edge-sites epic [#126](https://github.com/box1-org/box1-docs/issues/126)

**Dependencies:** none. This change blocks [#137](https://github.com/box1-org/box1-docs/issues/137) (`04_artifact_profile_quarkus_monorepo.md`) and [#138](https://github.com/box1-org/box1-docs/issues/138) (`05_vm_instance_profile_template.md`). It can run in parallel with #139 and #140, which touch other files.

## Mission

Replace the two-way `service` / `virtual-machine` switch in the onboarding plugin with a per-profile table of phase handlers. Adding the `artifact` and `vm-instance` profiles should then need only a table entry plus its handlers. **`service` and `virtual-machine` must behave exactly as before**: same bundles, PRs, records, markers, PipelineRuns and phase results.

## Verified baseline (observed 2026-11-08 on `box1-templates` main `5663eb3`; verify before relying on it)

All paths are in `box1-org/box1-templates`.

- **`plugins/box1-onboarding/workflow.cjs`**: about 755 lines with one `Workflow` class.
  - `PROFILES` (L22–25) holds only `templateVersion` and `commitMessage` for each profile.
  - The comment at L19–20 requires `service` to stay byte-for-byte compatible with records and markers written by earlier releases.
- **The boolean:** the constructor (L184) sets `this.vm=this.profile==='virtual-machine'`. The plugin branches on it in these places:

  | Line | What differs |
  |---|---|
  | L324 | `REQUESTED` record: VM adds `profile`; service has no `profile` key |
  | L328 | `.box1/onboarding.json` marker: VM adds `profile`; service keys are exactly `id,name,namespace,owner,templateVersion` |
  | L426 | `buildBarrier()` → `vmBuildBarrier()`: SA `ci-bootc-release`, image-builder binding, privileged SCC |
  | L440 | `platformReady()` check set → `vmPlatformChecks()` (serviceaccounts, registry pull/push subjects, last check `deployment` versus `virtual_machine`) |
  | L502 | `build()` PipelineRun spec: `box1-quarkus-maven` versus `vmBuildSpec()` (build → disk → channel) |
  | L522–523, L528 | build results: VM also requires `disk-digest`, and `IMAGE_BUILT` stores it |
  | L621 | `gitopsFiles()`: `validateBundle` versus `validateVmBundle` |
  | L652–668 | `promote()`: inline service edits versus `vmPromotionUpdates()` |
  | L682 | `verify()` → `vmVerify()` |

- **Code that does not branch:** `provision`, `platform`, `requestServiceSync`, `buildPhase`, `pullRequest` and `merge` (the required-check names at L401 apply to both profiles), `requestPromotionSync`, and the catalog methods.
  - PR titles and bodies say "service" for both profiles.
- **`registerCatalog()` (L703)** requires `this.data?.deploymentImage` plus merged onboarding and promotion PRs. Both verify paths set `deploymentImage`.
- **`plugins/box1-onboarding/index.cjs`:**
  - L8 hard-codes `enum:['service','virtual-machine']`.
  - The `box1:catalog:*` actions (L27–39) accept only `{name}`, so the profile defaults to `service`. This works today only because the catalog methods never call `requireProfile`.
  - `DELIVERY_PHASES` (L17) is `['provision','platform','buildPhase','promote','verify']`.
- **Tests** use `node:test` and run with `npm run validate && npm run test:onboarding && npm run test:onboarding-oci`. `validate` renders the fixtures under `.validation/` that the tests read. There are no golden or snapshot comparisons.
  - `scripts/test-onboarding.cjs` has about 45 service-only tests. L289–299 tie `DELIVERY_PHASES` to template step order and `index.cjs` text.
  - `scripts/test-onboarding-vm.cjs` has 12 tests, and some are **coupled to internals**:
    - L15 asserts `w.vm` and `deepEqual(PROFILES.service, …)`;
    - L71 calls `w.vmPlatformChecks()`;
    - L128 is a regex on the `index.cjs` enum text.
    
    These break under a table by design. Rewrite them deliberately and record why.
  - `scripts/validate.mjs` L201–285 renders `templates/rhel-image-vm` and calls `validateVmBundle`.
- **Release:**
  - `plugins/box1-onboarding/package.json` is `1.2.0`, and tag `onboarding-plugin-v1.2.0` already exists.
  - `.tekton/onboarding-plugin-release.yaml` runs on tag `onboarding-plugin-v<version>` (from `main` only): test → approve → publish by digest → `scripts/open-onboarding-gitops-pr.mjs`.
  - That script opens a `box1-gitops` PR that pins the digest in `platform/developer-hub/dynamic-plugins.yaml` (L13) and in the `box1.org/onboarding-plugin-digest` / `-revision` annotations in `platform/developer-hub/backstage.yaml`.
  - `box1-gitops/.tekton/onboarding-plugin-guard.yaml` refuses mutable references.
- **Docs:**
  - `plugins/box1-onboarding/README.md` L111–133, "Onboarding profiles (1.2.0)";
  - runbook `box1-docs/runbooks/rhdh-onboarding-plugin-oci.md`;
  - the VM regression procedure in `box1-docs/achievements/2026/2026-11-05-rhdh-vm-golden-path.md`.

## Decided design

The issue specifies this design. Confirm anything left open in Phase 1.

- `PROFILES` becomes the dispatch table. Each entry holds:
  - `templateVersion` and `commitMessage`;
  - the record and marker fields it adds;
  - `validateBundle`, `buildBarrier`, `platformChecks`, `buildSpec`, `buildResults`, `promotionUpdates`, `verify`;
  - a catalog completion predicate.
- **Optional phases are explicit.** For example, a profile with no GitOps workload declares `provision: false`, or `null` handlers, and skips `development:provision`. `registerCatalog` calls the profile's completion predicate instead of always requiring `deploymentImage`.
- The `index.cjs` enum is generated from `Object.keys(PROFILES)`. The default stays `service`.
- **Catalog actions and profiles.** The `box1:catalog:*` actions keep working without a `profile` input for existing templates. Decide whether they read the profile from the stored record or accept an optional input, and record the decision.
- **Service compatibility.** The service record and marker stay byte-for-byte identical, with no `profile` key. Keep the current failure messages unless a test proves a change is harmless.
- Do **not** add the `artifact` or `vm-instance` profiles here. Only prove the extension point, for example with a test-only profile.

**Not taken:** more nested `if (this.vm)` / `else if` branches for each new profile.

## Scope and guardrails

- **Characterisation test first.** Before changing any code, add a test that records, for `service` and `virtual-machine`:
  - the validated bundle result;
  - the files for the onboarding PR and the promotion PR;
  - the PipelineRun spec;
  - the build results stored;
  - the platform-check key list;
  - the verify sequence and saved outputs;
  - the record and marker.
  
  Commit it green on the old code, then keep it green through the refactor without editing its expectations.
- Rewrite only the coupled assertions listed above, with a commit message that explains each one.
- **Release:**
  - bump to the next minor version (expected `1.3.0`) in `package.json`, `oci-package.json` metadata, the README and `scripts/test-onboarding-oci.mjs` fixtures where they name the version;
  - merge to `main` (the user merges), then push the tag;
  - the release pipeline opens the `box1-gitops` pin PR, which the user merges.
- **After the pin merges:**
  - sync the `developer-hub` Argo Application. The user has given standing approval for this sync, after checking that no onboarding run is active (`rhdh` ConfigMaps `box1-onboard-*` and Leases);
  - confirm the running Pod loaded the new digest.
- No changes to templates, GitOps tasks or other repositories beyond the pin PR.
- Do not put test materials in `box1-gitops`. Run state and evidence go in `box1-docs`.

## Verifiable acceptance evidence

From the issue. Tick each item on #136 only with the evidence named.

- [ ] The `service` and `virtual-machine` profiles produce identical bundles, PRs and phase results before and after the refactor; plugin tests cover both.
  - *Evidence:* the characterisation test committed on the old code and passing unchanged on the new code, and the full `npm run validate && npm run test:onboarding && npm run test:onboarding-oci` output.
- [ ] A live regression onboarding of one Quarkus service and one RHEL image-mode VM succeeds on the new plugin digest.
  - *Evidence:* Hub task IDs, status records, the merged onboarding and promotion PRs, the verify outputs, and the Pod's loaded digest.
  - Both runs need approval, because onboarding creates repositories and deploys.
  - Use throwaway names, and decommission them afterwards per `runbooks/service-decommission.md` (needs approval).
- [ ] The plugin is published as a new OCI digest and pinned in `box1-gitops/platform/developer-hub/dynamic-plugins.yaml`.
  - *Evidence:* the release PipelineRun, the `inspect-onboarding-oci.mjs` output and the merged pin PR.
- [ ] Adding a profile needs only a table entry plus its handlers. This is documented in the plugin README.
  - *Evidence:* the README section, plus the test-only profile proving it.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Scope:** `plugins/box1-onboarding/*`, its tests and scripts, the README, the release, and the pin PR.

**Run state:** `box1-docs/agent-runs/136-onboarding-profile-dispatch/`.

**Discovery must cover:**
- current `main` of `box1-templates` (re-check every line reference above);
- the deployed plugin digest, from `dynamic-plugins.yaml` and the running Pod;
- the newest `onboarding-plugin-v*` tag;
- whether any onboarding run is active;
- the Hub action schemas, so the `index.cjs` enum change can be compared (`ACTION_SCHEMAS=<file> npm run validate`).

**Design decisions to record:**
- the handler interface and its names;
- how optional phases are expressed;
- how the catalog actions find the profile;
- the version number;
- the regression service and VM names.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Deployed digest and latest tag recorded; no active onboarding |
| 3 Implementation | Characterisation test committed before the refactor and passing after it, unmodified |
| 5 Review | Release and Operations passes confirm no service or VM output changed |
| 6 Delivery | New digest published and pinned; Hub restarted on it |
| 7 Live acceptance | Quarkus and VM regression onboardings succeed; regression resources decommissioned or deliberately kept as references |

**Verification scenarios:**
- an unknown profile is rejected;
- a profile mismatch with the stored record is rejected;
- resume after `PLATFORM_READY` and `IMAGE_BUILT` for both profiles;
- a `service` catalog step without a profile input still succeeds;
- the test-only profile, with no GitOps workload, skips provision and its catalog predicate passes without `deploymentImage`.

**Stop conditions:** in addition to the profile's own list:
- a refactor that cannot keep the characterisation test unchanged;
- the release pipeline refusing the tag;
- an active onboarding run when a restart is due.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md`, including the run state block. List:
- the characterisation test path;
- the plugin version and digest;
- the pin PR;
- the regression task IDs;
- the decommission state;
- the rollback digest, from the pin PR body.

Tick the completed acceptance items on #136. Leave #137 and #138 unblocked by naming the handler interface they must implement.
