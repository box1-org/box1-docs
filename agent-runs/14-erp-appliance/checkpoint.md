# Checkpoint: box1-docs#14 frontier run

Updated 2026-11-05 19:30 EST.

**Phase:** 6 complete. Phase 7 (VM and adapter acceptance) waits on #25 and #13; nothing in it is this run's to do alone.

## Done
- Phase 0: `evidence/00-discovery.txt`.
- Phase 1: `decisions/D-001`–`D-014`.
- Phase 2: ERP1 protocol, 65 fixtures, reference reader, result sequences, `UNREADABLE`, on `box1-ops-contracts` `legacy-erp-file-v1` at 13fcfd2, PR #6 merged by the user as eef13ea. Contract review repaired (`review-findings/00-contract-protocol.md`).
- Phase 3–4: local repo `run14-erp`; Phase 4 evidence `evidence/04-*.txt`.
- Phase 5: five reviewer passes (`review-findings/01`–`05`), 44 findings including one critical, all repaired in f15513c. Rerun: 152 tests, 44 harness checks (`evidence/05-after-review.txt`). Release pass not applicable.
- Handoff: `handoff.md`.

## Worktrees and local repos
- `/Users/mike/Documents/ChatGPT/box1/run14-docs` → box1-docs `agent-run/14-erp-appliance`
- `/Users/mike/Documents/ChatGPT/box1/run14-contracts` → box1-ops-contracts `legacy-erp-file-v1`
- `/Users/mike/Documents/ChatGPT/box1/run14-erp` → `box1-org/box1-ops-erp-simulator`, branch `erp-appliance` at d5b9cb2 (PR #1); `main` is the empty `db73db3`. (Local `main` still holds the pre-rebase history; use `erp-appliance`.)
- `/Users/mike/Documents/ChatGPT/box1/run14-gitops` → box1-gitops `erp-simulator-ci` (PR #61). `.venv` Python 3.12. Tests: `ERP1_CONTRACTS_DIR=../run14-contracts .venv/bin/pytest -q`. Harness: `python -m build --wheel . && harness/run-scenarios.sh <scratch dir>`.

## Since the stop
- User merged box1-ops-contracts#6 (eef13ea); `contracts.lock` repinned.
- User created the repository. Code pushed: `main` = empty `db73db3`, PR #1 from `erp-appliance` (`d5b9cb2`).
- box1-gitops#61 (PaC registration) open; its 2 checks pass.

- User merged box1-gitops#61 and box1-ops-erp-simulator#1 (`bfc262f`). First release `…-release-9jvng` and PR run `…-pr-d8bmw` failed in `fetch` (root-owned working directory, see pilot-log repair 16). Fix: box1-ops-erp-simulator#2 at `193ba70`.

- User merged #2 (`c84c910`). Release `box1-ops-erp-simulator-release-5dgjm` succeeded: 154 tests in-cluster, pushed `box1-ci/box1-ops-erp-simulator@sha256:34053e1b1b6ac8aeb7d8f497c7d21f63ef89ad9f2a9693c1acb420d127b01aab` with the scoped Role, security gates (observe) scan-exit=0, policy=pass, SBOM in TPA (`evidence/06-release.txt`). Ledger: 23 ci_verified.

## Open decisions (user)
None. Follow-ups: give the digest to #25; #13 consumes ERP1 from contracts main.

## Risks
- The pipelines and the name-scoped push Role have never run in the cluster.
- Unit sandboxing and the console on a real TTY are unverified (harness limits); #25 must verify.

## Exact next action
None for this run until #25 or #13 report. Then: rerun the VM criteria with #25's evidence, tick #14 boxes with stated proof levels, and close the run.
