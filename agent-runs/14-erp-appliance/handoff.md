# Agent handoff: box1-docs#14, frontier run

Updated 2026-11-05 19:30 EST. Phase 6 complete: the artifact is published by digest through the reviewed pipeline. Phase 7 waits on #25 and #13.

## Work completed
- **Service / platform workstream:** Service 04, Python legacy ERP appliance (#14), frontier profile.
- **Slice / requirements:** the whole prompt up to the VM boundary. Ledger: 26 `locally_tested`, 2 `implemented`, 3 `blocked`, none higher (`requirements.yaml`).
- **Repository and branch:**
  - `box1-org/box1-ops-contracts`, branch `legacy-erp-file-v1` at `13fcfd2`: [PR #6](https://github.com/box1-org/box1-ops-contracts/pull/6), open and mergeable, not merged.
  - `box1-org/box1-ops-erp-simulator` **does not exist yet** (D-001). The code is a local git repository at `/Users/mike/Documents/ChatGPT/box1/run14-erp`, branch `main`, commit `f15513c`, with no remote. **It exists only on this workstation.**
- **Changed paths:** contracts: `legacy/erp-file/v1/**`, `test/erp-file.test.mjs`, `package.json`, `README.md`. ERP: `src/box1_erp/*`, `tests/*`, `systemd/*`, `packaging/*`, `config/*`, `harness/*`, `docs/*`, `.tekton/*` (drafts), `pyproject.toml`, `contracts.lock`, `catalog-info.yaml`, `README.md`.
- **PR / commit (actually created):** box1-ops-contracts#6 (3 commits: b6e6731, b20694c, 13fcfd2). No ERP PR: no repository.

## Tests and deployment proof
- **Exact commands and observed results** (`evidence/05-after-review.txt`):
  - contracts `npm test`: 75 pass, 0 fail.
  - ERP `ruff check src tests`: clean.
  - `ERP1_CONTRACTS_DIR=../run14-contracts .venv/bin/pytest -v`: 152 passed, covering fixtures, domain, worker, a pseudo-terminal console at 80x24, backup and restore, and review regressions.
  - `harness/run-scenarios.sh`: 44 passed, 0 failed (CentOS Stream 10, systemd 257, OpenSSH SFTP, a podman data volume).
  - A 50-round two-process ship race: worker won 31, console 19, always one shipment (`evidence/04-local-tests.txt`).
- **CI status:** none. box1-ops-contracts has no CI; the ERP repository and its CI need D-001 and D-002.
- **GitOps PR and deployed image digest:** none. The appliance is not deployed by Argo; the VM is #25.
- **Routes / endpoints verified:** none by design. The ERP has no HTTP interface.

## Contract state
- **OpenAPI / event schemas changed:** none. New: ERP1 file protocol v1 with 65 golden fixtures, `sequences` for result ordering, and an event-to-file mapping.
- **Database migrations and forward compatibility:** SQLite schema v1 (`user_version`). Opening a ledger at another version is refused; `box1-erp migrate` brings an older one up under an exclusive lock.
- **Consumer compatibility / pending follow-up:** #13 consumes ERP1 unchanged and must write its own framing step; SPEC section 9 explains why Camel Bindy alone cannot. `contracts.lock` pins the PR head and **must be repinned to the merge commit** after #6 merges.

## Operations and safety
- **Secrets externalized / auth boundaries:** no credentials anywhere. The SFTP account is key-only and chrooted, with no shell, no access to the state directory and no handle on archived files. The harness key is generated per run in the session scratchpad. The console is unauthenticated by design; the RUNBOOK trust model says RBAC on the VM console (#25) controls it.
- **Telemetry evidence:** JSON lines to journald with millisecond timestamps, `request_id`, `file_id`, `correlation_id` and `traceparent`. `box1-erp status --check` exits 0/1/2 and reports lag ages.
- **Resource settings:** worker `MemoryMax=256M` (peak observed 10.6 MB), console `128M`. Proposed VM: 1 vCPU, 1 GiB RAM, 2 GiB data disk (`docs/VM-INTEGRATION.md`).
- **Known risks and recovery/rollback:**
  - The code exists on one workstation until D-001.
  - Twelve seccomp-based sandbox directives, plus SystemCallFilter, ProtectProc and ProcSubset, were disabled by a harness-only drop-in.
  - The console unit never ran on a real TTY.
  - The drafted pipelines have never run.
  - Recovery: the runbook covers restart, broken console, quarantine and replay, backup, restore with divergence, upgrade and migrate, and guest rebuild.

## Next agent session
- **Next smallest slice:** after D-001, push `run14-erp` to the new repository, repin `contracts.lock` to #6's merge commit, and open the first PR. After D-002, open the box1-gitops PR and get the PR pipeline green. Then a release publishes the artifact digest for #25.
- **Exact files to read (not whole repo):** this `handoff.md`, `checkpoint.md`, `decisions/D-001`, `D-002`, `D-011`; in the ERP repository `docs/VM-INTEGRATION.md` and `.tekton/`.
- **Blockers and required user decisions:**
  1. Merge box1-ops-contracts#6, which unblocks #13 and #25.
  2. D-001: create `box1-org/box1-ops-erp-simulator`, public, with `gh repo create`.
  3. D-002: approve opening a box1-gitops PR for the PaC Repository CR plus a non-privileged `ci-erp-release` service account.
- **What #25 and #13 must show to close #14's VM boxes:** the tables in `docs/VM-INTEGRATION.md`, mirrored on issue #14.

## Run state (`frontier` only)

```yaml
profile: frontier
issue: box1-org/box1-docs#14
current_phase: 7   # blocked on #25 (VM) and #13 (adapter)
repositories:
  - name: box1-org/box1-ops-contracts
    branch: legacy-erp-file-v1
    commit: 13fcfd23038c95fcf4ec0306a932596890e577e4
  - name: box1-org/box1-ops-erp-simulator (local only, no remote)
    branch: main
    commit: f15513c
  - name: box1-org/box1-docs
    branch: agent-run/14-erp-appliance
    commit: (this push)
run_state_path: agent-runs/14-erp-appliance/
requirements:
  proposed: 0
  implemented: 2
  locally_tested: 5
  ci_verified: 23
  deployed: 0
  live_verified: 0
  blocked: 1
  superseded: 0
image_digest: sha256:34053e1b1b6ac8aeb7d8f497c7d21f63ef89ad9f2a9693c1acb420d127b01aab  # box1-ci/box1-ops-erp-simulator, source c84c910
gitops_commit: null
review_passes_completed: [contract-protocol, architecture, persistence, messaging, security, operations]   # release: not applicable
open_decisions: []
rollback_state: nothing deployed or merged; closing PR #6 and deleting branch legacy-erp-file-v1 reverts all shared changes
next_action: give the digest to #25; resume Phase 7 when #25/#13 report evidence
```

## Update 2026-11-05 19:30 EST

All three approvals happened: box1-ops-contracts#6 (`eef13ea`), box1-gitops#61, box1-ops-erp-simulator#1 and #2 (`c84c910`). The first release runs failed in `fetch` (root-owned working directory, fixed in #2). Release `box1-ops-erp-simulator-release-5dgjm` then passed: 154 tests in the cluster, image `box1-ci/box1-ops-erp-simulator@sha256:34053e1b1b6ac8aeb7d8f497c7d21f63ef89ad9f2a9693c1acb420d127b01aab`, security gates in observe mode with `scan-exit=0`, `policy=pass` and an SBOM in TPA (`evidence/06-release.txt`). The sections above predate this and describe the earlier stop.
