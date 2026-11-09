# Edge sites 08 — greenboot health checks and automatic rollback for site releases

> **Edge release safety in the site image and the release path.** An OS image that is unhealthy after boot rolls itself back, and a bad release never reaches the second site. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Deliberately shipping a bad release to a site is a fault injection: approval needed, `site-east` only, never `site-west`.
- Promotions go through GitOps PRs. The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not touch `legacy-erp` or `vm-golden-check`.
- Do not use Chrome.

**Issue:** [box1-docs#133](https://github.com/box1-org/box1-docs/issues/133), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- `01_site_foundation.md`: the `site-gateway-os` image, units and persistent data.
- [#137](https://github.com/box1-org/box1-docs/issues/137): the bundle by digest, so one OS digest covers OS and apps.
- [#138](https://github.com/box1-org/box1-docs/issues/138) and [#139](https://github.com/box1-org/box1-docs/issues/139): per-instance approved digests and the `vm-instance` promote target.
- [#141](https://github.com/box1-org/box1-docs/issues/141) (`../03-golden-path/06_staged_site_rollout.md`): the staged rollout and the digest-pinned switch that applies a release in an instance guest. #141 lists this issue as a dependency, and this issue needs #141 for its staged criteria. Run #141's mechanism first; the bad-release criterion is then proved once and may tick both issues. Without #141, prove greenboot rollback on `site-east` with an approved manual `bootc switch` and stop at the staged-promotion part.
- `04_site_status_sites_map.md`: the heartbeat that reports the running digest and greenboot status to the console.

## Mission

Add greenboot required checks to `site-gateway-os` so that a release whose site services are unhealthy after boot rolls back automatically to the previous deployment, reports the rollback, and keeps buffered site data. Releases reach `site-east` first and `site-west` only after `site-east` verifies.

## Verified baseline (observed 2026-11-09; verify before relying)

- **greenboot is not used anywhere** in `box1-org`; no `/etc/greenboot/check/required.d` exists. Whether `rhel-bootc:10.2` ships greenboot is **not verified**.
- The `rhel-image-vm` Containerfile **disables `bootc-fetch-apply-updates.timer`**; upgrades are applied by the pipeline.
- **`box1-bootc-apply`** (`box1-gitops/platform/pipelines/tasks/bootc-apply.yaml`, namespace `box1-ci`): gets `virtctl` from the CNV download Service (L81–105); `virtctl ssh` as `box1-deploy` with a key Secret kept outside Git, host keys trusted on first use (L110–122); reads the booted digest from `bootc status --format json` (L124–129); runs `bootc upgrade --apply` (L140–147); **waits until the booted digest equals `image-digest`** (L148–155); checks the default target and listed units (L157–170). It runs as SA `ci-vm-deploy`, granted per workload (`box1-workloads-dev/workloads/legacy-erp/deploy-access.yaml` L17–53).
- **`box1-bootc-apply` is not the apply step for instances.** `bootc upgrade` follows the shared channel tag that `box1-bootc-disk` recorded, so instances need a digest-pinned `bootc switch` (`box1-gitops/platform/pipelines/GOLDEN-PATH.md`, "Channels"), which #141 adds. A `vm-instance` day-2 promotion changes only the instance's annotations (#139 decision D-006). `box1-bootc-status` (read-only, optional `expected-digest`) reads the booted digest.
- `legacy-erp`'s sudoers allow `box1-deploy` only `bootc upgrade --apply` and `bootc status --format json`.
- `box1-vm-smoke` checks the approved digest, not the booted one (`vm-smoke.yaml` L1–5).
- On 2026-11-05 upgrade and rollback were exercised manually only ([VM golden path achievement](https://github.com/box1-org/box1-docs/blob/main/achievements/2026/2026-11-05-rhdh-vm-golden-path.md) L97–99, L135).
- #139's owner decision: instances pin digests only; each promotion changes one instance's `os-image-digest` annotation and DataVolume digest.

## Decided design

From the issue and #126's golden-path decisions.

- `site-gateway-os` installs greenboot and adds **required** checks: the `site-gateway` and `site-ops` health endpoints, the AMQ Broker MQTT listener, PostgreSQL reachability, and outbox Flyway migrations applied. Each check has a bounded wait so slow starts do not cause false rollbacks.
- When a required check fails, greenboot reboots into the previous deployment (boot counter and rollback configured and documented).
- After a rollback the site agent reports the running digest and greenboot status (`04`), and the console shows them.
- Each site has its own approved digest in `box1-workloads-dev`, applied in the guest through the release path. The issue says `bootc upgrade --apply`, but on an instance that would follow the shared channel tag, so the apply is #141's digest-pinned `bootc switch --apply`.
- **Staged rollout (#141):** a release reaches `site-east` (`site_spacedock`) first; it is promoted to `site-west` (`site_ds9`) only after `site-east` verifies, including greenboot.
- **Interaction with the rollout (#141):** after an automatic rollback the booted digest never equals the approved digest, so the stage's verify fails. That failure must stop promotion to `site-west` and leave a clear message. #141 decides how the instance's annotation in Git is then reconciled; agree that the greenboot status it reads is the one this prompt configures.
- Buffered site data lives on persistent storage chosen in `01`, so it survives the upgrade and the rollback. Flyway migrations in a release must stay compatible with the previous version, because a rollback runs old code on the new schema.

## Scope and guardrails

**In scope:** greenboot package, checks and configuration in `site-gateway-os`; the greenboot status that #141's verify step and the site agent (`04`) read; the release and rollback runbook in `box1-docs/runbooks/`.

**Out of scope:** the staged-rollout mechanism itself (#141), unless that issue is folded in by the owner; changes to `legacy-erp`.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #133 only with the evidence named.

- [ ] A good release reaches `site-east`, verifies, then reaches `site-west`, all through GitOps, and the console shows the new digest on each site.
  - Evidence: the two promotion PRs in order, the rollout's per-stage verify results, `bootc status` from both guests, and the console. Needs #141.
- [ ] A deliberately bad release, one that fails a greenboot required check, is rolled back automatically on `site-east` and is never promoted to `site-west`. The console shows the previous digest and the rollback, and the site resumes reporting.
  - Evidence: the bad change (for example a health endpoint that fails), the approved promotion to `site-east`, greenboot journal lines, `bootc status` after rollback, the failed rollout stage, no `site-west` promotion, and the console.
- [ ] Buffered site data survives the upgrade and the rollback.
  - Evidence: outbox depth and a marker row before the upgrade, after it and after the rollback; the backlog later drains (`02`).
- [ ] The release and rollback procedure is in a runbook.
  - Evidence: the merged runbook path.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/133-site-greenboot/`.

**Discovery must cover**
- greenboot availability and version on RHEL 10 bootc, and how it triggers rollback with bootc.
- #139's promote target and #141's state.
- How #141's switch and verify steps behave when the booted digest does not match.
- The site migrations' backward compatibility.

**Design decisions to record**
- Check list, timeouts and boot-counter settings.
- How a rollback blocks the next stage.
- How Git is reconciled after a rollback.
- How the bad release is produced and cleaned up.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 4 Verification | Rollback proven on a test VM before touching `site-east` |
| 6 Delivery | Good release on both sites through GitOps (or `site-east` only, marked `blocked` on #141) |
| 7 Live acceptance | All four criteria, or the staged parts recorded as blocked |

**Verification scenarios**
- A check that times out rather than fails; the broker slow to start; a rollback followed by a second bad release; a reboot of a healthy deployment does not roll back; data written during the bad boot.

**Stop conditions**
- greenboot is unavailable for RHEL 10 bootc.
- A bad release would have to be applied to `site-west` to prove a criterion.
- #141's rollout is not delivered (stop at the staged criteria only).

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the checks, configuration, digests, the runbook, evidence, what #141 still needs, and rollback (re-promote the previous digest; greenboot itself reverses a bad boot).

Tick the completed items on #133.
