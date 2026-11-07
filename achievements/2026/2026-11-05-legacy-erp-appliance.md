# Legacy ERP appliance: file protocol, application and pinned release under the frontier profile

**Date:** 2026-11-05 (America/New_York)
**Status:** Built, reviewed, released through CI and published by digest. **Not yet running in a VM**: boot-to-console, reboot and the adapter round trip belong to [#25](https://github.com/box1-org/box1-docs/issues/25) and [#13](https://github.com/box1-org/box1-docs/issues/13), so [box1-docs#14](https://github.com/box1-org/box1-docs/issues/14) stays open with every checkbox unticked. Full run state, decisions, evidence and review findings are in [`agent-runs/14-erp-appliance/`](../../agent-runs/14-erp-appliance/).

## Outcome

The legacy side of the modernization demonstration now exists. It is a Python ERP appliance with a curses operator console, a background worker and a SQLite ledger. It talks to the modern world only through versioned, pipe-delimited files over SFTP. There is no HTTP API, OpenAPI document or Kafka integration, by design.

```text
protocol   box1-org/box1-ops-contracts legacy/erp-file/v1 (merged eef13ea)
source     box1-org/box1-ops-erp-simulator c84c910
artifact   image-registry.openshift-image-registry.svc:5000/box1-ci/box1-ops-erp-simulator@sha256:34053e1b1b6ac8aeb7d8f497c7d21f63ef89ad9f2a9693c1acb420d127b01aab
release    PipelineRun box1-ops-erp-simulator-release-5dgjm (box1-ci): 154 tests passed, pushed, security gates observe: scan-exit=0, policy=pass, SBOM in RHTPA
```

The artifact is a one-layer OCI image with no base. It carries the wheel (standard library only, Python 3.12), the two systemd units, the provisioning script, the sshd reference and the runbooks. It is not meant to run: #25's bootc build copies it in by digest.

Merging the protocol first unblocked [#13](https://github.com/box1-org/box1-docs/issues/13) (adapter) and [#25](https://github.com/box1-org/box1-docs/issues/25) (VM), as the run order required.

This was the third run under the `frontier` execution profile, after [order-service](2026-11-05-order-service-delivery.md) and [inventory-service](2026-11-05-inventory-service.md). It was the first that was not a Quarkus Golden Path service and not deployed by Argo CD.

## Starting baseline

Observed at about 17:35 EST (`evidence/00-discovery.txt`):

- No ERP repository existed in `box1-org`. The prompt proposed `box1-ops-erp-simulator`.
- `box1-ops-contracts` had no legacy protocol. `fulfillment.requested.v1` carries a single `sku` and `quantity`, and `order-service` bounds IDs at `ful_`/`shp_` + 124 characters.
- There was no CI path for a non-Quarkus repository:
  - The two templates are Quarkus or no-build.
  - No repository in the org used GitHub Actions.
  - `box1-security-gates` scans only image digests.
  - The internal registry is the only artifact store.
- `rhel-image-poc` (#46) had just shown a bootc build with inline Tekton tasks, running privileged.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `box1-ops-contracts` | [#6](https://github.com/box1-org/box1-ops-contracts/pull/6) | `eef13ea` | ERP1 protocol v1 and its specification, plus 65 golden fixtures, result-ordering sequences, the `fulfillment.requested.v1` mapping and a reference reader for `npm test`. No event schema changes |
| `box1-gitops` | [#61](https://github.com/box1-org/box1-gitops/pull/61) | `d3d7d6b` | Pipelines as Code `Repository`; `ci-erp-release` ServiceAccount; the `box1-ops-erp-simulator` ImageStream; a Role allowing push to that one ImageStream only. Nothing privileged |
| `box1-ops-erp-simulator` | [#1](https://github.com/box1-org/box1-ops-erp-simulator/pull/1) | `bfc262f` | The application, tests, systemd units, packaging, container harness, docs and `.tekton/` pipelines |
| `box1-ops-erp-simulator` | [#2](https://github.com/box1-org/box1-ops-erp-simulator/pull/2) | `c84c910` | Pipeline fix for the first in-cluster failure (below) |

The user created the repository and merged every PR. Because the repository started empty, its `main` begins with one empty commit (`db73db3`), so the code could arrive by PR.

**Decisions with consequences.** There is one record each in `decisions/` on the run branch.

- **Protocol (D-003 to D-007, D-013).** ERP1 is UTF-8 with backslash escaping and a fixed validation order, so the Python ERP and the Camel adapter report the same error code. It allows 1 to 99 line items; a v1 event maps to one, and nothing is dropped. Equivalence ignores origin, timestamps and trace context, so REST and Kafka submissions of the same request match. Each state change produces a result with a random ID and a per-request revision; consumers order by revision, never by file name. Section 9 records that Camel Bindy alone cannot read ERP1, so #13 needs its own framing step.
- **Ledger (D-008).** SQLite with WAL, `synchronous=FULL`, a bounded `busy_timeout` and `BEGIN IMMEDIATE`. Every rule lives in one domain module that the console and the worker both call. A `UNIQUE` constraint backstops one shipment per request.
- **Durability (D-009).** Results are written to a temp file, `fsync`ed, renamed, and the directory `fsync`ed; only then is the result marked published. Requests are committed before their files leave the exchange.
- **Demo faults (D-010).** They are enabled only in the root-owned config. A one-shot crash disarms in its own committed transaction before the process exits, so a restart cannot loop.
- **Delivery (D-002, D-011).** Pipelines as Code with inline tasks, as in rhel-image-poc, but unprivileged: Python assembles the image and `skopeo` pushes it with the service account's token. #25 pins the digest.
- **Storage.** One data volume at `/srv/box1-erp` holds `state/` (private) and `exchange/` (the SFTP chroot), so every file move is a rename. User and group IDs are fixed (961 to 963), so a rebuilt guest owns the kept data.

## Validation and evidence

| Check | Result | Proof level |
|---|---|---|
| Protocol fixtures | Node reference 75/75 (`npm test`), Python reader all fixture checks. A mutation check showed the tests fail when expectations are wrong | Local |
| Every verification scenario in #14 (manual vs automatic ship race; repeated and conflicting IDs; hold, release, reject; re-emit; crash after commit; paused and delayed processing; malformed, truncated and temp-name files; quarantine and replay; worker stopped under the console; console restarted under the worker; 80x24 and resize; mode persistence; backup and restore; SFTP denied the database) | 154 pytest tests, including the console under a pseudo-terminal and real subprocess crashes. The ship race over 50 extra rounds: worker won 31, console 19, always one shipment | Local, then **CI**: the same 154 passed in release `…-5dgjm` |
| Container harness (CentOS Stream 10, systemd 257, OpenSSH SFTP, a data volume) | 44/44. Covers SFTP isolation, key-only access with no shell; attacks by the SFTP account (a symlink to the ledger, a mode-000 file, an inbound link) with the ledger intact; crash recovery under systemd; the watchdog restarting a frozen worker; fixed IDs; backup and restore with record checks | Local container |
| Six reviewer passes (contract, architecture, persistence, file exchange, security, operations) | 60 findings (one a note): 1 critical, 10 high. All repaired; the suite and harness reran | Review |
| Release `box1-ops-erp-simulator-release-5dgjm` | Tests, push with the name-scoped Role, security gates: `scan-exit=0`, `policy=pass`, SBOM accepted | Cluster (CI) |
| Unit hardening | `systemd-analyze security --offline`: worker 1.1, console 1.3 (OK) | Local |

**Not established:**
- Anything in the VM: boot to the console on `ttyS0`, SELinux enforcing, reboot, and guest rebuild with the kept volume.
- 15 sandbox directives (the seccomp-based ones plus `ProtectProc` and `ProcSubset`). Rootless Podman cannot run them, so the harness turned them off in a labelled drop-in (`harness/worker-harness-only.conf`).
- The console unit on a real TTY.
- A request through #13 and a result consumed by it.
- A passing PR pipeline run: every PR run so far predates the pipeline fix.

**Most useful repairs**, all found before release:

- **Critical, from the security pass.** A symlink the SFTP account planted at the predictable outbound temp name was followed on the next republish, overwriting the ledger. An equivalent repeat request was enough to trigger it. 133 tests had not treated the exchange as hostile. Now there are random temp names with `O_EXCL|O_NOFOLLOW`, inbound entries are copied into application-owned files, and unreadable entries are quarantined unopened. The last of these needed a new protocol error code, `UNREADABLE`, added before #6 merged.
- **Restore under a running console split the ledger** (three passes found it independently). Restoring an older backup also allowed a second shipment. Restore now needs an exclusive ledger lock, refuses to roll back past newer shipments or revisions unless told to, keeps the previous ledger, and starts in MANUAL mode.
- One unreadable or oversized inbound file stopped all ingestion. A quarantine name was not idempotent across a crash. A failed `COMMIT` kept the write lock.
- The console crashed at start on a `vt100` terminal, and its ledger row was 85 columns wide.

**The first in-cluster runs failed in `fetch`** with `Permission denied: source/.gitignore` (runs `…-9jvng`, `…-d8bmw`, `…-gtxst`; nothing was pushed). The cause: Tekton creates all step containers at pod start, and the container runtime creates a missing `workingDir` as root. The later steps' `workingDir: /workspace/source` therefore existed, root-owned, before the non-root fetch step ran. The same script, image and tarball worked locally because only one container ran at a time. rhel-image-poc uses the same layout but runs as root. Reproduced with Podman, fixed in #2, and guarded by a test. Because Pipelines as Code runs pipeline definitions from `main`, only the release after merge could prove the fix; it passed on the first run.

## Final operational state

- **Published:** `box1-ci/box1-ops-erp-simulator@sha256:34053e1b…aab` (tag `c84c910d…`), from source `c84c910`; wheel sha256 `faa0fd21…1760`.
- **CI:** Pipelines as Code runs the PR pipeline as `ci-test` and the release as `ci-erp-release`, from `box1-gitops` `platform/pipelines/ci/box1-ops-erp-simulator.yaml`, managed by Argo CD Application `pipelines-ci`, which has no automated sync.
- **Security gates** run in `observe` mode, not `gate`, as in rhel-image-poc.
- **Not deployed anywhere.** No VM, cluster workload or Argo Application runs the ERP.
- **No temporary workarounds** in source or on the cluster. The harness drop-in exists only in the test harness.

## Recovery and follow-ups

- **Rollback:**
  - Revert `box1-gitops#61` and sync `pipelines-ci` to remove the registration, service account, Role and ImageStream. **Not exercised.**
  - The published image stays until the ImageStream is deleted.
  - Nothing consumes it yet, so there is nothing to roll back at runtime.
- **Operations:** the repository's [runbook](https://github.com/box1-org/box1-ops-erp-simulator/blob/main/docs/RUNBOOK.md) covers health, restart, a broken console, quarantine and replay, backup, restore and divergence, upgrade and `migrate`, and guest rebuild.
- **[#25](https://github.com/box1-org/box1-docs/issues/25):**
  - Build the guest from the digest above, following [`docs/VM-INTEGRATION.md`](https://github.com/box1-org/box1-ops-erp-simulator/blob/main/docs/VM-INTEGRATION.md). It lists the install steps, the storage layout, the proposed size (1 vCPU, 1 GiB RAM, 2 GiB data disk) and exactly what the VM must show to close #14's boxes.
  - This includes the sandbox directives and TTY behaviour the harness could not test.
- **[#13](https://github.com/box1-org/box1-docs/issues/13):** consume ERP1 from `box1-ops-contracts` main unchanged; the adapter needs its own framing step.
- **#14:**
  - Remains open.
  - The [status comment](https://github.com/box1-org/box1-docs/issues/14#issuecomment-6672462245) gives each criterion's proof level, and predates the release; 23 of the 31 ledger entries are now `ci_verified`.
  - The run-state branch is not merged.
- **Process lessons** are in the run's `pilot-log.md`:
  - A hostile-input threat model belongs in the test plan, not only in review.
  - Several containers in one pod behave differently from one container at a time.
  - A pipeline change can be proven only after merge when Pipelines as Code takes definitions from `main`.
