# Golden path 06 — Staged per-site OS rollout (`site-east`, then `site-west`)

> **This is a golden-path change, not a new service.** It turns one OS release into an ordered, verified rollout across the `vm-instance` instances of a source image, and adds the missing step that moves an instance's guest onto its pinned digest. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- `box1-gitops-promote` and `box1-gitops-validate` gate every release. A bad change blocks all releases; keep the `service`, `virtual-machine` and first-promotion `vm-instance` paths unchanged.
- A new guest command, SSH key or sudoers rule is a new permission: approval needed, and the key is created outside Git.
- Deliberately failing a rollout stage is a fault injection: approval needed, `site-east` only, never `site-west`.
- Changes go through PRs. The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Put test materials and run state in `box1-docs`, not `box1-gitops`.
- Do not touch `legacy-erp` or `vm-golden-check`. Do not use Chrome.

**Issue:** [box1-docs#141](https://github.com/box1-org/box1-docs/issues/141), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- [#139](https://github.com/box1-org/box1-docs/issues/139) (`02_gitops_vm_instance_validate_promote.md`) and [#138](https://github.com/box1-org/box1-docs/issues/138) (`05_vm_instance_profile_template.md`): the `vm-instance` promote target, `box1-bootc-status` and the instance template. Their code is merged; their live acceptance is not done.
- `site-gateway-os` and the instances `site-west` and `site-east` (`../04-edge-sites/01_site_foundation.md` and #138). Until they exist, prove the mechanism with two throwaway instances of a test source image (approval required), or stop at the live criteria.
- [#133](https://github.com/box1-org/box1-docs/issues/133) (`../04-edge-sites/08_site_greenboot_rollback.md`) supplies the greenboot checks. The issue lists #133 as a dependency, and #133 needs this rollout for its staged criteria. Build the rollout mechanism here first, with a verify step that already reads greenboot status. The bad-release criterion is then proved together with the #133 run, and either run's evidence may tick it.
- [#130](https://github.com/box1-org/box1-docs/issues/130) (`../04-edge-sites/04_site_status_sites_map.md`) supplies "site reporting" and the console digests. Without it, verify the booted digest and greenboot only, and record the reporting check as `blocked`.

## Mission

When `site-gateway-os` releases a new OS digest, promote it to `site-east` (`site_spacedock`) first, apply it in that guest, and verify it (booted digest matches, greenboot healthy, site reporting). Only then promote, apply and verify `site-west` (`site_ds9`). A failed verify, including a greenboot rollback, stops the rollout, records why, and leaves later sites on their current digest. The order is declared in Git and can change without pipeline code changes.

## Verified baseline (observed 2026-11-09; verify before relying)

`box1-gitops` main `c121614`, `box1-templates` main `d4e2364`, `box1-workloads-dev` main `34dc9a9`.

**What merged on 2026-11-09** (issues still open, nothing live-verified): `box1-gitops#132` (validate and promote for `vm-instance`), `#133` (bundle Tasks), `#134` (#140 validator rules, `box1-bootc-status`), `#136` (onboarding plugin 1.5.0); `box1-templates#33`–`#37` (profile dispatch, cloud-init, `quarkus-monorepo`, `vm-instance`). `site-gateway`, `site-gateway-os`, `site-west` and `site-east` do not exist yet.

**Promotion (`platform/pipelines/tasks/gitops-promote.yaml`, `GOLDEN-PATH.md` L260–320)**
- `workload-profile: vm-instance` with `instance-name`; `application-name` is the source repository, whose `main` must still equal `revision`.
- One promote Task promotes one instance: branch `promote/<instance>/…`, files under `workloads/<instance>/` only, and a sync of that instance's Argo Application. Other instances are never read or changed. `development` auto-merges after the required checks pass on the exact head.
- **Day 2 changes only annotations** (`os-image-digest`, `source-revision`, `build-pipelinerun`; `plan_instance_updates` L155–184). The DataVolume digest is not swapped, because CDI rejects DataVolume spec updates. This is decision D-006 in the #139 run state ([PR #145](https://github.com/box1-org/box1-docs/pull/145)), which says: "In-guest upgrade to the pinned digest is #141."

**Applying a digest in the guest: the missing step**
- `box1-bootc-apply` (`tasks/bootc-apply.yaml` L7, L144) runs `bootc upgrade --apply`, which pulls the **channel tag**.
- `box1-bootc-disk` records `box1-ci/<source>:<channel>` as the update source, and every instance shares that disk. On an instance, `bootc upgrade` would therefore follow the shared tag, not the instance's pinned digest. `GOLDEN-PATH.md` L352–362 states the requirement: a digest-pinned switch in the guest, for example `bootc switch …/box1-ci/<source>@sha256:<instance digest>`, with the automatic update timer disabled. The `rhel-image-vm` Containerfile already disables `bootc-fetch-apply-updates.timer`.
- `box1-bootc-status` (`tasks/bootc-status.yaml`) is read-only. It runs as `ci-vm-deploy` with the key Secret `box1-ci/vm-instance-status-ssh` (created outside Git; **not yet created**) and guest user `box1-status`, whose key is forced to `sudo /usr/bin/bootc status --format json`. Its `expected-digest` param makes it a gate. The instance bundle's Role `<instance>-status-reader` grants `get` on the VMI and `virtualmachineinstances/portforward`.
- `GOLDEN-PATH.md` says `box1-deploy` must not be used on instances, because its contract allows `bootc upgrade --apply`.

**Release pipeline** (`templates/rhel-image-vm/skeleton/.tekton/release.yaml`): `build` → `security` → `disk` → `promote` (the source's **own** VM, profile `virtual-machine`) → `channel` → `smoke`. Nothing promotes instances. A repository created from `rhel-image-vm` therefore also has its own VM, `<source>` in `<source>-dev`.

**Ordering today:** nothing orders promotions across instances, and no rollout declaration exists in any repository.

## Decided design

From the issue and #126's golden-path decisions (staged per site: `site-east` first, then `site-west`; instances pin digests only).

**Rollout declaration (in Git)**
- An ordered list of stages per source image. Proposed: `box1-workloads-dev/rollouts/<source>.yaml`, next to the instances it orders, for example `stages: [site-east, site-west]` plus a per-stage soak time. Record the location, and record the alternative (the source repository) as not taken or chosen.
- `box1-gitops-validate` checks it: every listed instance exists, is `vm-instance`, and carries `box1.org/source-image: <source>`; no duplicates. An instance missing from the list is not rolled out automatically; record whether that is an error or a warning.
- Changing the order is a Git change only (acceptance criterion 3).

**Rollout runner**
- Triggered after the source release succeeds, with the source revision, image digest and disk digest. Decide the mechanism and record it. Options:
  - (a) a `box1-vm-rollout` Task or Pipeline that reads the declaration and, for each stage in turn, creates a child PipelineRun (promote → apply → verify) and waits for it;
  - (b) generated per-stage tasks in the source's release pipeline, which would put the order in pipeline code and so fail criterion 3.
  - Recommended: (a). Any Tekton object it needs is added in `box1-gitops/platform/pipelines/`, and the `rhel-image-vm` template's release pipeline gains one final task that starts it when the repository has a rollout declaration.
- Each stage:
  1. **Promote:** `box1-gitops-promote` with `workload-profile: vm-instance` and `instance-name: <stage>`, which opens and auto-merges the per-instance PR and syncs Argo.
  2. **Apply:** a digest-pinned switch in the guest (below).
  3. **Verify:** `box1-bootc-status` with `expected-digest`; greenboot status healthy for the new boot; and, once #130 is delivered, asset-service `GET /api/v1/sites/{siteId}` online and reporting the new digest. Verify waits for a stated soak time, so a greenboot rollback that happens after the reboot is caught.
- **Stop on failure:** the runner fails, names the stage and the failed check, and starts no later stage. Record the failure on the stage's promotion PR (a comment) as well as in the PipelineRun, so it is visible from Git. Later instances keep their digests.
- **After a rollback**, the instance's annotation records the new digest while the guest runs the old one. Decide how Git is reconciled: an automatic revert PR, or a documented manual revert. Never leave it unrecorded.
- **The source's own VM:** decide whether it is stage 0 (a canary without site identity), excluded, or not created for `site-gateway-os`. Coordinate with `../04-edge-sites/01_site_foundation.md`, because that VM costs capacity.

**Digest-pinned apply (new)**
- A new Task (proposed `box1-bootc-switch`), or a new mode of `box1-bootc-apply` that leaves its current behaviour byte-identical. It runs `bootc switch --apply image-registry.openshift-image-registry.svc:5000/box1-ci/<source>@sha256:<digest>`, then waits for the guest to boot that digest.
- **Guest contract:** a dedicated user (proposed `box1-rollout`), provided by the source OS image, whose authorized key is forced to a fixed wrapper (for example `/usr/libexec/box1/switch-to-digest`). The wrapper accepts only a `sha256:<64 hex>` argument, builds the reference from a fixed registry and source, and runs `bootc switch --apply`. sudoers allows only the wrapper. It must not be `box1-deploy` or `box1-status`.
- **Cluster contract:** the instance bundle grants `ci-vm-deploy`, or a dedicated ServiceAccount, the same VMI and portforward access as `<instance>-status-reader`. The key Secret is created outside Git (approval). If the `vm-instance` template or validator must change for this, do it here, with tests, and keep the existing outcomes for existing workloads.

## Scope and guardrails

**In scope**
- `box1-workloads-dev`: the rollout declaration for `site-gateway-os`.
- `box1-gitops`: the declaration check in `gitops-validate`, the rollout runner, the switch Task, tests, and `GOLDEN-PATH.md`.
- `box1-templates`: the `rhel-image-vm` release hook and the guest user and wrapper (opt-in, so existing repositories render byte-identically), plus any `vm-instance` bundle grant.
- `box1-docs`: run state, and a runbook section on reading, pausing, resuming and re-running a rollout.

**Out of scope**
- greenboot checks themselves (#133).
- The site status API (#130).
- Changing `legacy-erp`, `vm-golden-check` or their pipelines.
- Rollback of a healthy release by policy (manual re-promotion stays the procedure).

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #141 only with the evidence named.

- [ ] A good release goes to `site-east`, verifies, then goes to `site-west`. Both PRs and verifications are recorded.
  - Evidence: the source release PipelineRun; the rollout run; the two promotion PRs with merge times in order; each stage's `box1-bootc-status` result (`booted-digest` equal to the release digest), greenboot status and, if #130 is delivered, the site status response; and `site-west`'s digest unchanged until `site-east` verified.
- [ ] A bad release that fails greenboot on `site-east` is rolled back there and never promoted to `site-west`. The console shows both digests.
  - Evidence: shared with #133's run. The approved bad release, greenboot rollback journal lines, the failed stage and its reason (PipelineRun and PR comment), no `site-west` promotion PR, the Git reconciliation of `site-east`'s annotation, and the console showing each site's running digest (needs #130).
- [ ] The rollout order can be changed in Git without changing pipeline code.
  - Evidence: a PR changing only the declaration (for example `site-west` first, on a test source or with a no-op release), the validator result, and a rollout run that follows the new order. Restore the owner's order afterwards.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/141-staged-site-rollout/`.

**Discovery must cover**
- Current `main` of `box1-gitops`, `box1-templates` and `box1-workloads-dev`, and the open run-state PRs for #136–#140.
- Whether D-006 was accepted by the owner.
- `bootc switch` behaviour on RHEL 10 bootc with a digest reference: the update source it records, and whether a later `bootc status` reports the digest the rollout expects.
- How greenboot reports a successful or rolled-back boot (#133's choice), and how long a rollback takes after reboot.
- Whether `site-gateway-os` exists, and whether it has its own VM.
- Every caller of `box1-gitops-promote` and `box1-bootc-apply`, so their behaviour stays unchanged.

**Design decisions to record**
- Declaration location and schema; runner mechanism; soak time; the guest user, wrapper and key; the ServiceAccount; failure recording; Git reconciliation after a rollback; the source VM's role.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 0 Discovery | `bootc switch` to a digest tested on a throwaway VM (approval), not assumed |
| 3 Implementation | Validator tests for the declaration; existing promote and validate suites unchanged and passing |
| 4 Verification | Stop-on-failure proven with a failing verify on a throwaway instance |
| 6 Delivery | `box1-gitops` and `box1-templates` changes merged by the user; Argo shows the new Task revisions |
| 7 Live acceptance | The three criteria, with criterion 2 marked as shared with #133 |

**Verification scenarios**
- The second stage's instance is missing or Halted.
- A verify timeout.
- The source main moves during the rollout (promote's superseded-revision check fails the stage).
- The rollout is re-run for the same digest: already-verified stages are skipped or re-verified, never re-applied blindly.
- Two releases in quick succession.
- The wrapper is given a tag or another repository: rejected.
- The automatic update timer is confirmed disabled on instances.

**Stop conditions**
- `bootc switch` to a digest does not work on the installed bootc.
- The guest user, key or ServiceAccount is not approved.
- A change would alter the outcome of an existing workload's validation or promotion.
- No instances or throwaway instances are available for live acceptance.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List:
- the declaration file and schema;
- the runner and switch Task, with an example invocation;
- the guest contract that `site-gateway-os` must provide, handed to `../04-edge-sites/01_site_foundation.md` and #133;
- the evidence for each criterion;
- what #133 still needs;
- rollback: revert the `box1-gitops` and `box1-templates` PRs. Already-applied instances keep their digest; re-promote the previous digest to move one back.

Tick the completed items on #141.
