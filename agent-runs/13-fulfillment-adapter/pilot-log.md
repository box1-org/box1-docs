# Frontier profile pilot log: box1-docs#13

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 1 | 2026-11-05 20:20 EST | 6 entry | Platform conflicts with the prompt; next actions need approval; a dependency is unavailable | Phases 0–5 are finished. The adapter has no database (D-012). Every remaining step is a merge, a sync, a new credential, or a write to a shared topic: D-002, D-007, D-009, D-012, D-015. The ERP VM (#25) does not exist. |

| 2 | 2026-11-05 21:15 EST | 7 | Requirements cannot be proven with available evidence; next actions need approval | Deployed and live-checked with the user's approvals (merges, one KafkaTopic sync). A live fulfillment needs D-002 or D-015; SFTP and the VM boxes need #25 and D-007. |

No stop fired earlier. Discovery found the database conflict in Phase 0. It blocks only Phase 6, so I finished independent work first, as the pilot rule asks.

## Repairs

Found by verification (Phase 4), fixed and retested:

1. **Kafka rejections were recorded without the request ID.** When an event failed ERP1 carriability checks inside the parser (quantity over 999,999,999, a control character in `sku`), the durable `rejected_command` row had no `fulfillmentRequestId`, so an operator could not find it by request. `KafkaInputTest` caught it. The poison exception now carries the event and request IDs when they are well formed.
2. **A gauge and a counter shared a Prometheus name.** `fulfillment_needs_attention` (gauge) and `fulfillment_needs_attention_total` (counter) collide in the Prometheus registry. The first request to enter needs-attention would have thrown inside the result transaction and rolled it back. `ResultIngestionTest` caught it; the counter is now `fulfillment_needs_attention_entries_total`, and the test asserts every metric renders.
3. **Upload failures did not say why.** `lastError` held the Camel wrapper class, so a host-key rejection looked like an outage, and the host-key scenario's first pass (run 1, 46/46) proved less than it claimed. Root causes are now fixed categories (`HOST_KEY_REJECTED`, `CONNECTION_CLOSED`, ...), and the scenario asserts the category.
4. **Rootless Podman turns "refused" into "closed".** With `sshd` stopped, the port forwarder accepts and then drops the connection; JSch reports `connection is closed by foreign host`. Run 2 (45/46) failed on my assumption; I read the cause with a JSch probe before changing anything, then added `CONNECTION_CLOSED`.

Found by reviewer passes (Phase 5), fixed and retested. See `review-findings/`:

5. **ERR-driven resends never stopped** (High; found independently by the persistence and messaging passes). An upload reset the counter the ERR resend used, and the resend had no backoff, so a deterministic transport `ERR` would loop upload → ERR every second forever. It now has its own counter, backoff, and `ERR_RESENDS_EXHAUSTED`. I had no test for repeated ERRs; there is one now.
6. **A REST failure would echo `Authorization` and a stack trace** (security). Camel `platform-http` copies message headers into the response, even on unhandled exceptions. Fixed with route-scoped handlers. **My first fix was itself dangerous:** I made the handler global, which on `erp-results` would have marked a failed commit as handled and moved the file to `consumed/` with no record. I caught it while restructuring the routes, before any run.
7. **Outbound files were read whole**, so a huge file could crash-loop the pod. Reads are now bounded to 65,537 bytes.
8. **Camel's SFTP consumer never lists dot-names.** This was a reviewer's unverified concern. The harness confirmed it (run 4b, 49/50), and the new `outbound-hidden-sweep` route quarantines such files and moves them.
9. **Some database outages dead-lettered valid events** (credentials, read-only primary, commit-time rollback). These are now treated as outages that hold the channel. Every dead-letter path also writes a durable record, and an interrupt no longer dead-letters.
10. Smaller fixes: claims scoped to the stored backend; legacy types moved behind an architecture test; a late upload failure can no longer overwrite a result; receipts deduplicated; bulk reconcile; metrics freshness and publish lag; runbook replay steps; shutdown drain; a lease that outlasts a batch.

Two reviewer suggestions were not valid for Camel 4.22: `muteExceptions` on `platform-http` and `includeHiddenFiles` on `sftp`. Each failed at startup, and I read each cause before changing anything (one cause, not a cascade). The full suite and scenarios were rerun after all repairs: 123 tests + 5 ITs, 50/50 scenario checks, TUI 6/6.

Test-harness mistakes, not product defects: a test expected `FIELD_VALUE` for a ten-digit quantity where ERP1 checks length first (`FIELD_LENGTH` is right); the release smoke task first landed in the pipeline `results` list (caught by parsing the YAML); the TUI driver omitted Enter after `Y`, and the audit query used the wrong column names.

## Profile ambiguity and friction

6. **Getting a user token was the slowest step of live acceptance.** I first suggested the admin console's Evaluate tab. In RH-SSO 7.6 it shows only decoded claims, not a usable token. The user then ran a PKCE script by hand. The run may not hold user credentials, so an operator-run helper is the right shape; it is now proposed in fulfillment-adapter#2.

3. **"Each ERR code the adapter can provoke."** The adapter validates every file before upload, so the real ERP can only produce `CONFLICTING_REUSE` (by a second writer) from it. I fed the other codes to the ingestion path as ERP-format ERR files and recorded that in the ledger, rather than writing a deliberately broken uploader.
4. **"Crash between result commit and the rename."** The only observable effect of that crash is redelivery of the same file. I proved the redelivery outcome and did not try to time a kill between two statements. The ledger says so.
5. **Same-model reviewers found real defects that 119 tests and 46 scenario checks missed** (findings 5 and 6). Both were in paths I had no adversarial test for. Running the passes after Phase 4, as the rule says, meant they reviewed the commit I kept.

1. **The prompt's starting state was wrong on one fact that matters.** It says the adapter's workload includes `postgres.yaml` from the template pattern; the file is empty and not referenced, because the repository was onboarded with PostgreSQL off. The profile's "nothing assumed from prompt text" rule caught it in Phase 0, before any design depended on a database Secret existing.
2. **"Read the prompt from `fulfillment-adapter-review` if PR #53 is still open."** It merged at 18:48 EST, four minutes before this run started, so I read `main` (`fe81297`).

## Places I was unsure of my authority

3. **"Do the merges" did not cover the `box1-kafka` sync.** Your instruction listed Argo syncs separately, so I merged the three PRs that need no sync first. I asked once, with the exact resource and with prune off, before syncing and merging #1. The Argo auto-sync of `fulfillment-adapter` after each merge is the Application's own policy, not an action I took.
4. **Checking the database Secret.** I confirmed that it exists and listed its key names only, without reading any values.

1. **Building the ERP harness.** The run may run the #14 ERP from its local repository, but building it writes `dist/` into that repository. I build from a local clone (`run13-erp-src`) instead, so `run14-erp` is never written.
2. **Standing developer-hub sync memory.** Workspace memory holds a standing approval to sync `developer-hub`. This run's instruction requires explicit approval for each Argo sync; the narrower instruction wins, and no step needs that Application.

## Did earlier pilots' lessons prevent repeats?

| Lesson | Applied here | Result |
|---|---|---|
| CI has no container runtime | `containers` tag and `-Pcontainers`, copied from inventory | **Prevented.** PR CI passed first time. |
| Template ships `security-gates: disabled` (#42) | Set `gate` in `.tekton/release.yaml` before the first PR | **Prevented**, not yet exercised (runs on merge). |
| ConfigMap literal changes orphan hashed ConfigMaps | Runtime settings will be Deployment `env` entries | Not yet exercised (no workloads PR). |
| Database outage dead-letters valid events | Inventory D-007 hold-the-channel logic reused; storage-down scenario | **Prevented** for REST (503) and the consumer path; Kafka-during-outage not separately exercised. |
| DLQ send failure crash-loops the pod | DLQ topic made a merge prerequisite (D-009) | Not yet exercised. |
| Clock domains | All schedules use database `now()` | **Prevented**; no clock-related failure. |
| Laptop sleep and VM clock drift | Clock check before and after every long run; `caffeinate -ims` | No sleep or drift observed (host and VM agreed in every check). |
| Leaked processes cause cascades | Adapter started and killed by PID file only; containers named `run13-*` | **Prevented.** Each failure had one cause, read before changing anything. |
| Reviewer passes started too early | Reviewers start only after Phase 4 | **Prevented.** All six reviewed `8f576d5`, and the repairs went into one commit. |
| The release gate depends on working dependencies (order run) | Checked the gate's own run, not only pod health | **Passed.** The first gated release on this image succeeded (`kz42z`, security step Succeeded). |
| DLQ must exist before the service ships (inventory run) | Synced the topic, with approval, before merging #1 | **Prevented.** The topic was Ready before the first consumer start. |
| Rerun the full suite after review repairs | Suite, scenarios and TUI rerun on `11778f8` | **Applied.** |
| Approvals cover only what they name | Each pending action listed separately | Applied. |

## Building against a protocol another run designed

- **The spec was enough to build from.** SPEC sections 1–7 are precise about order of checks, lengths and outcomes. My reader passed all 84 fixture checks on its first run, and the first real upload was imported by the ERP without an `ERR`. Nothing in this run needed an ERP1 change.
- **Fixtures with expected outcomes did most of the work.** The `sequences` entries turned section 7 into executable cases. I ran them twice: against the pure rule function, and through the database-backed consumer.
- **The protocol's recovery primitive shaped the adapter.** "An equivalent repeat republishes the latest result" (section 6) gave one mechanism for lost uploads, lost results, transport-damage `ERR`s and slow probes. I did not have to design a status query.
- **What the spec leaves to the consumer.** It does not say how the adapter should treat each `ERR` code, how long to wait for revision 1, or what to do with results after `CONFLICTING_REUSE`. Those became D-004 and D-005. Without the ERP as a test partner, I would have guessed that a request from another writer produces results the adapter has never sent. In fact it does, and section 7 correctly quarantines them as `UNKNOWN_REQUEST`.
- **Running the other run's harness as a test partner was cheap.** Its `domain` API and documented keys let me hold, release, ship and reject, inject faults, and drive the real TUI by keystrokes. Its scripts hard-code `run14-*` names, so I wrote my own launcher rather than edit it.
- **The other run kept moving.** Between discovery and the first build, the ERP moved from a workstation-only repository (`f15513c`) to `box1-ops-erp-simulator` (`c84c910`), and its `contracts.lock` was repinned to the same commit as mine. I rebuilt from the published repository so the evidence names a durable commit.

## Environment findings

- **I recorded estimated times instead of reading the clock.** The first Phase 6 records said 20:28–20:32 EST for events that happened by 20:20. A clock check at the next wakeup caught it, and I corrected the times from commit timestamps. The rule I now follow is to read `date` before writing any time.

- Podman VM: 4 CPU / 8 GiB, shared with run15's three containers; my stack (`run13-pg`, `run13-kafka`, `run13-erp`, plus `run13-tc-*` during tests) fit without memory pressure.
- Host and Podman VM clocks agreed at every check from 18:52 to 19:46 EST. **The laptop slept from about 19:55 to 19:56:50 EST** (`pmset` log). The Podman VM then ran 76 s behind the host. The full-suite run that followed failed on an unrelated cause, which I read first. The skew did not affect results: scheduling uses PostgreSQL's clock inside the VM, and token checks use the host's. I did not reset the shared VM clock because #14 and #15 containers run in it. It had resynchronised by 20:08 EST.

## Side effects outside the run state

- `git fetch` in the user's `box1-docs` and `box1-ops-contracts` clones (remote refs only; checkouts untouched).
- New worktrees: `run13-docs` (branch `agent-run/13-fulfillment-adapter`), `run13-contracts` (detached at `eef13ea`). New clones: `run13-fulfillment-adapter`, `run13-erp-src` (`box1-ops-erp-simulator` at `c84c910`).
- The ERP wheel was built with the Python in `run14-erp/.venv` (read-only use; nothing written inside `run14-erp`).
- Containers and volumes: `run13-pg` (:25432), `run13-kafka` (:29092), `run13-erp` and volume `run13-erp-data` (:22213), image `localhost/run13-erp-harness:dev`; transient `run13-tc-pg` and `run13-tc-kafka` from Testcontainers.
- Issue #13: one [comment](https://github.com/box1-org/box1-docs/issues/13#issuecomment-6674063802) with the proof level for every criterion. I ticked 12 boxes at Local or CI level; the VM round trip, the VM TUI shipment and "through the Route" stay unticked.
- Left running for resumption: containers `run13-pg`, `run13-kafka`, `run13-erp` (about 1.6 GiB in the shared Podman VM). The adapter JVM is stopped. Remove with `podman rm -f run13-pg run13-kafka run13-erp && podman volume rm run13-erp-data`.
- Opened box1-gitops#69 (Keycloak client `fulfillment-adapter`) at the user's request, and merged it with approval (`60cf703`); Argo `keycloak` synced it automatically.
- Opened the achievement log [box1-docs#58](https://github.com/box1-org/box1-docs/pull/58) (`achievements/2026/2026-11-05-fulfillment-adapter-delivery.md`); not merged.
- Opened [fulfillment-adapter#2](https://github.com/box1-org/fulfillment-adapter/pull/2) (`scripts/operator-login.py`, runbook) at the user's request after the manual token steps proved tedious; not merged.
- With approval: merged box1-ops-contracts#8 (`d21d91f`), box1-gitops#64 (`0f5ff2d`), box1-workloads-dev#65 (`ff2595b`) and fulfillment-adapter#1 (`0a44cc6`); synced the single KafkaTopic `box1.fulfillment.dlq.v1` through the `box1-kafka` Application's operation field (prune off). The release pipeline then auto-merged promotion PR box1-workloads-dev#73 (`3668f3b`). Second issue comment and the Route box ticked at cluster level.
- Pushed branches and opened PRs (merged later, see above): box1-ops-contracts#8 (`fulfillment-dlq-v1`), box1-gitops#64 (`fulfillment-dlq-topic`), box1-workloads-dev#65 (`fulfillment-adapter-database`). Worktrees `run13-gitops` and `run13-workloads` from the user's clones.
- Pushed branch `fulfillment-adapter-v1` and opened [fulfillment-adapter#1](https://github.com/box1-org/fulfillment-adapter/pull/1) (not merged). Its PR pipeline `box1-ci/fulfillment-adapter-validate-cvgl9` ran in the shared CI namespace.
