# Frontier profile pilot log: box1-docs#14

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 2 | 2026-11-05 19:05 EST | 6 | Next action needs approval | User created the repository and asked for the PaC PR; both PRs opened. Merging and syncing box1-gitops#61, then merging the ERP PR, each need approval. |
| 1 | 2026-11-05 18:55 EST | 6 entry | Next action needs approval | Merging box1-ops-contracts#6, creating the ERP repository (D-001) and CI in box1-gitops (D-002) each need approval. Phases 0 to 5 finished first; the protocol PR was reported ready at about 18:00 EST. Phase 7 also needs #25 and #13, which start only after the merge. |

## Repairs

Found by the contract review of PR #6 (before Phase 4, by design: see ambiguity 3), fixed and retested: 15 findings, 3 high. The most consequential were no rules for conflicting or late results, which #13 needs, and a version check that would have trapped any v2 header change. See `review-findings/00-contract-protocol.md`.

Found by verification (Phase 4), fixed and retested:

1. **The console crashed at start on a `vt100` terminal.** `curs_set(0)` raises where the terminal cannot hide the cursor. A serial console can be exactly that, so the appliance could have booted into a restart loop. Now cosmetic.
2. **The ledger row was 85 columns.** `UPDATED` and the publication column were cut off at 80. Found by asserting the header's last column in the pty test, not by looking.
3. **The rejection code needed Enter after the digit.** Changed to a one-key menu; the test exposed it.
4. **Conflict quarantine was two transactions.** The import recorded the conflict and a later call wrote the quarantine record, so a crash between them could leave one without the other. Merged into the import transaction.

Found by reviewer passes (Phase 5), fixed and retested. Five fresh-context passes found 44 findings, about 25 distinct; all repaired in f15513c. See `review-findings/01`–`05`:

7. **Critical: the SFTP account could overwrite the ledger.** A symlink planted at the predictable outbound temp name was followed on the next republish, which an equivalent repeat request triggers without any operator action. The Security pass demonstrated it. Now random temp names opened with `O_EXCL|O_NOFOLLOW`; the harness repeats the attack over real SFTP and the ledger stays intact. **133 passing tests and 29 harness checks had not considered the exchange hostile.**
8. **One unreadable or oversized inbound file stopped all ingestion** (mode 000 set by the SFTP client blocked every later file; a large upload exceeded `MemoryMax` and restarted forever). Messaging and Security, independently.
9. **Restore under a running console split the ledger.** Architecture, Persistence and Operations all found it independently; two reproduced it. Restore to an older point also allowed a second shipment and reused revisions, and my runbook said the opposite. Now a ledger lock and a divergence check.
10. **Quarantine was not idempotent across a crash** (clock in the stored name). Found by three passes.
11. Fixed IDs, a storage layout one volume can hold under sshd's chroot rules, watchdog and restart backoff, schema version and migrate, `status --check`, a failed COMMIT holding the write lock, missing ledger columns, a TUI that bypassed the domain's demo gate, and smaller items.
12. **My first repair introduced a drift.** I added `UNREADABLE` to the specification but not to the Python reader, so the worker wrote `ERR` files its own reader rejected. The regression tests caught it; a new test now compares the reader's code lists with SPEC.md.
13. **A packaging line that never ran:** `u box1erp 962:962` in sysusers requires an existing group, so the image build failed. Found only by building the image.

The full suite (152 tests) and the harness (44 checks) were rerun after the repairs, as the issue's Phase 5 exit requires.

Harness repairs, not product defects:

5. **Rootless Podman cannot run systemd's seccomp-based sandboxing for a user-switching service** (status 217/USER). Fourteen harness checks failed from this one cause. I read the journal, then bisected with probe units: twelve directives fail alone. A labelled harness-only drop-in disables exactly those; the shipped unit keeps them, and #25 must verify them in the VM.
6. One test expected the file outcome `CONFLICT`; the code records `QUARANTINED:CONFLICTING_REUSE`, which is more useful. Test corrected.

## Profile ambiguity and friction

1. **The profile assumes a service repository already exists or comes from Golden Path onboarding.** Its authority table pairs "creating a repository" with onboarding. For a Python appliance, neither the Quarkus template nor the onboarding plugin fits (#46 records why), so creation is a plain `gh repo create` that still needs approval. Independent work (protocol, local implementation) continued under "a stop blocks dependent work".
2. **Phase 6 assumes an image, a promotion PR and Argo.** This appliance has no cluster deployment; its delivery is a pinned artifact for #25. The issue's phase-exit table replaces it, but the profile's Release reviewer pass (digest in GitOps, Argo revision, running pod) has nothing to check.
3. **Reviewer timing for a shared contract.** The request says reviewer passes start after Phase 4. The protocol is the first deliverable and blocks two other runs, so I ran one contract review on PR #6 before asking for its merge. It reviews the commit intended to be kept, which is the reason the request gives for the timing rule.

4. **`ci_verified` presumes CI exists.** For a new repository with no CI path in the platform, the highest reachable level is `locally_tested` until a shared-repository change is approved.
5. **Container harness versus the profile's "local fault injection with Testcontainers".** The profile's local-test row assumes Testcontainers or Dev Services. A systemd-in-Podman harness is the nearest equivalent here, and it could not exercise part of the units' sandboxing.
6. **The Release reviewer pass has nothing to check.** No image, GitOps change or deployment exists; recorded as not applicable.
7. **Phase 7 assumes the run can reach live acceptance.** Here every VM criterion depends on another run (#25) that cannot start until this run's protocol merges. The run's furthest point is a handoff, not live evidence.

## Places I was unsure of my authority

1. **Developing without a repository.** Creating `box1-ops-erp-simulator` needs approval, so the code lives in a local git repository with no remote. That is independent work under "a stop blocks dependent work", but it leaves the implementation on one workstation until you approve D-001.
2. **A throwaway SSH key for the harness.** The harness generates an ed25519 key per run in the session scratchpad and installs its public half in the test container. It was issued by this run for this run, is never committed, and grants nothing outside the container.

## Did earlier pilots' lessons prevent repeats?

| Earlier lesson | Applied here | Result |
|---|---|---|
| CI has no container runtime, so container-backed tests stay `locally_tested` | Container-free unit, pty and subprocess tests; container only for the systemd/SFTP harness | **Partly.** Most of the suite needs no container, but there is no CI at all yet (D-002), so nothing is `ci_verified` |
| Reviewers in parallel with Phase 4 caused stale findings | Implementation reviewers start only after the Phase 4 commit | Applied. The one early review was of the protocol PR at its intended commit |
| Repin a service pinned to an unmerged contracts commit | `contracts.lock` says it pins the PR head and must be repinned | Pending the merge |
| Laptop sleep | Clocks checked before the harness runs; runs kept short (about 1 min each) | No sleep observed so far |
| Leftover processes from other runs | Not touched; only `run14-*` containers, removed by the script | Applied. The 5 order-run JVMs are still running |
| Live writes to shared systems need approval | None made: the cluster was not touched | Applied |
| Reviewers find defects tests miss (order log, repairs 5 to 9) | Five passes, fresh context, after the Phase 4 commit | **Repeated, at a larger scale.** The critical finding was a whole threat model (a hostile SFTP account) that neither tests nor I had applied. Three passes independently found the restore split |
| One cause looks like many failures | 14 harness failures read as one cause before any change | **Prevented a wrong fix.** My first guess (namespace directives) was wrong; the journal and probe units found seccomp |
| Pod health is not a functional check (order log 14) | The harness checks behaviour (SFTP denial, result files, record equality), not unit state alone | Applied |

14. **My drafted pipelines would have failed on their first run.** The pinned UBI 10 Python image has no `tar` or `gzip`, and the release used unprivileged buildah, which the restricted SCC most likely blocks. Found by running the steps in the real image before opening the PR, not by reading them. Replaced with Python extraction and a Python-built OCI layout pushed by `skopeo`.
15. **Emulation is not evidence.** The pinned amd64 image runs here only under QEMU, where `ruff` segfaulted (exit 139). I ran the arm64 build of the same tag instead and say so in the PR; the first in-cluster run is the real check.

16. **The first in-cluster runs failed in `fetch`: `Permission denied: source/.gitignore`.** The user merged box1-gitops#61 and box1-ops-erp-simulator#1 (`bfc262f`); the release and a PR run both failed identically. The same script, pinned image (Python 3.12.15) and GitHub tarball succeeded locally. Cause, found by comparing with the Quarkus task and then reproduced with podman: Tekton creates all step containers at pod start, and the runtime creates a missing `workingDir` as root, so `/workspace/source` (the later steps' working directory) existed root-owned before the non-root fetch ran. rhel-image-poc, the pattern I copied, runs as root and never showed it. **My local checks ran one container at a time, so they could not find a fault that comes from several containers sharing a pod.** Fixed in box1-ops-erp-simulator#2 with a guard test. Because PaC takes pipeline definitions from `main`, no PR can test a pipeline fix; only the run after merge proves it.

17. **The fix worked first time after merge.** Release `…-5dgjm` passed every step, including the untested name-scoped push Role. A PR run (`…-gtxst`) on the fix's head failed the old way, as the PR said it would, because PaC runs `main`'s definitions.

## Environment findings

- Host and Podman VM clocks agreed at 22:36 UTC.
- Five `quarkus-run.jar` processes from the order run are still running. Not touched.

## Side effects outside the run state

- `git fetch` in the `box1-docs`, `box1-ops-contracts` and `order-service` clones; the discovery subagent fetched `box1-templates`, `box1-gitops`, `quarkus-reference`, `box1-workloads-dev` and `rhel-image-poc`. Checkouts were not changed.
- New worktrees `run14-docs`, `run14-contracts`; new local repository `run14-erp` (no remote).
- `uv` installed a Python 3.12.12 toolchain in the user's uv cache.
- `npm ci` in the `run14-contracts` worktree.
- Pushed `box1-ops-contracts` branch `legacy-erp-file-v1` (2 commits); opened `box1-ops-contracts#6` and edited its description twice.
- Local Podman: pulled `quay.io/centos/centos:stream10`; built image `localhost/run14-erp-harness:dev`; containers `run14-erp-harness` and `run14-erp-debug`, both removed. `dnf` inside the image build downloaded CentOS packages.
- Installed `pytest`, `ruff`, `build` and `pyte` into `run14-erp/.venv`.
- One desktop notification attempt (not sent: Remote Control inactive).
- Pushed box1-ops-contracts `13fcfd2` (`UNREADABLE`); the first push was rejected by GitHub (`commit_refs_rules`, then a 502 on the PR edit), the retry succeeded. PR #6 description edited again.
- Local Podman: pulled `registry.access.redhat.com/ubi10/python-312-minimal` and `ubi10/ubi-minimal` (amd64) to read their digests for the drafted pipelines; created and removed volume `run14-erp-data`; rebuilt `localhost/run14-erp-harness:dev`; probe units inside a `run14-erp-debug` container (removed).
- Reviewer subagents worked in scratch extracts under the session scratchpad; the security pass wrote a PoC script there.
- Posted a status comment with proof levels on box1-docs#14 (issuecomment-6672462245). No checkbox ticked: every result is local or harness proof and nothing is merged.
- The user merged box1-ops-contracts#6 (eef13ea) and created `box1-org/box1-ops-erp-simulator`.
- Pushed to `box1-ops-erp-simulator`: `main` = one empty commit `db73db3` (an empty repository has no branch for a PR to target), and branch `erp-appliance` (`d5b9cb2`, the run's commits rebased onto it, tree unchanged). Opened `box1-ops-erp-simulator#1`.
- New worktree `run14-gitops`; pushed `box1-gitops` branch `erp-simulator-ci`; opened `box1-gitops#61`. Its two PaC checks ran in `box1-ci` and passed.
- Local Podman: pulled `ubi9/skopeo` (amd64) and `ubi10/python-312-minimal:latest` (arm64); ran throwaway containers to check image tools, the fetch helper (downloaded the public contracts tarball) and the PR test step (installed dev dependencies from PyPI).
- Read-only cluster checks: `oc get application`, `oc get imagestream -n box1-ci`, `oc get clusterrole system:image-builder`; one `oc auth can-i --as` (answered no, likely for lack of impersonation rights).
- The user merged box1-gitops#61 and box1-ops-erp-simulator#1. Runs `box1-ops-erp-simulator-release-9jvng` and `box1-ops-erp-simulator-pr-d8bmw` in `box1-ci` failed in `fetch`; logs and pod specs read with `oc` (read-only). No images were pushed.
- Opened box1-ops-erp-simulator#2 (first diagnostics, then the fix; branch `ci-fetch-diagnostics`). Its PR run uses `main`'s pipeline and is expected to fail the same way.
- Local podman: volume `run14-wd-test` (removed) to reproduce the root-owned working directory.
- **A mistake:** I ran a bare `git stash` in `run14-erp`, which stashed my uncommitted pipeline fix. I restored it at once with `git stash apply <sha>` and dropped that entry; `run14-erp` is a standalone clone, so no other checkout's stash was affected, and the stash is empty again. I also wrote one file to `/tmp` and deleted it.
- The user merged box1-ops-erp-simulator#2 (`c84c910`). Release `box1-ops-erp-simulator-release-5dgjm` pushed one image to `box1-ci/box1-ops-erp-simulator` and uploaded one SBOM to TPA.
