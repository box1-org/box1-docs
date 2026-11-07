# Frontier profile pilot log: box1-docs#12

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 1 | 2026-11-05 17:10 EST | 6 entry | Next action needs approval; product decisions required | Every remaining step is a merge, a sync, or a live write. D-002 needs the user's review before the first deploy, and D-010 and D-011 are open. Phases 0 to 5 finished first. |

| 2 | 2026-11-05 22:25 UTC (17:25 EST) | 7 | Next action needs approval | User approved the merges and sync, and "do what you think best" for decisions. Merges, sync and release done. Creating a live order through the Order Route was denied by the session's permission check, because the approval did not name it. |

No stop fired earlier. Discovery found no conflict needing the user: the repository name came with the request, and the contract gaps were additive.

## Repairs

Found by verification (Phase 4), fixed and retested:

1. **An unparsable floor did not stop the application.** The floor was a String parsed in the consumer's constructor. CDI builds that bean lazily, so `INVENTORY_ORDER_EVENTS_FLOOR=yesterday` left a running process with a dead consumer that could still report ready. It was the silent failure the offset policy exists to prevent. The missing-value case passed; only the bad-value case found it. The floor and TTL are now typed config values, validated at startup.
2. **Test harness: a failed assertion left an application running.** It held Kafka partitions, and two later tests timed out. One real cause looked like three failures, the same pattern the order run recorded.
3. **Test bug:** an immutability check updated zero rows, so the trigger never fired.

Found by reviewer passes (Phase 5), fixed and retested. See `review-findings/`:

4. **Expiry could beat an unread fulfillment signal after an outage or restart, sending a healthy order to `EXCEPTION`.** Found independently by Architecture and Messaging. Added `ExpiryGate`. One case remains: a reservation unpublished past its `expiresAt` by a long broker outage, which is Order's own rule.
5. **A database outage dead-lettered valid events after about 7 minutes.** The order run's fix for a 7.5 s bound was a longer bound, and reviewers showed the bound itself is the hazard for `fulfillment.requested.v1`. An unavailable database now holds the channel without using attempts.
6. **A late shipment took stock again on every redelivery.** Found independently by Architecture and Persistence.
7. A shipment for a different fulfillment request consumed a committed hold. History could record a stale previous status. Roles could come from a top-level `groups` claim. Permanent data errors retried for 7 minutes. The parser was looser than the contract.
8. **My first fix for the roles finding ran after body binding,** so a wrong-role token got a 400, not a 403. Moved to an identity augmentor.
9. Documentation: no first-deploy merge order, no lag measure, a replay procedure that could not be run as written, and a wrong runbook line on what Order sees after a release.

The full suite was rerun after the repairs: 81 tests, 0 failures, as the issue's Phase 5 exit requires.

Local saga script repairs, mine, not product defects: Kafka listener for in-container tools, a metric exemplar parse, a lost tab in an unquoted `$(printf '\t')`, a test TTL shorter than a cold Order's round trip, and a load step that inherited the 3 s TTL.

## Profile ambiguity and friction

1. **Reviewer timing.** I ran five reviewer passes in parallel with the end of Phase 4. They were reading a commit while I fixed a Phase 4 defect, so one finding was already fixed when it arrived. The profile orders the phases, but parallel review shortened the run. The Release pass waits for deployment.
2. **A contract pin to an unmerged commit.** "No local copy of a shared schema" is met by fetching from the contracts PR head. If the merge rewrites the commit, the service must be repinned before it merges.
3. **`ci_verified` for a partial suite.** CI has no container runtime, so it runs only the container-free tests. I kept the scenarios at `locally_tested` and marked only `INV-CI` as `ci_verified`. The order run reported the same friction.
4. **Live acceptance writes to shared systems.** Phase 7 requires one real order through the Route. That creates order data and produces to shared topics, which the user's instruction puts under approval. The profile's authority table does not list it.
5. **Is a review finding about another service in scope?** The saga showed Order's consumer leaving its group during a database outage. That is evidence about Order, found by this run's test, and an Order change is a stop. I reported it and did not investigate further.

## Places I was unsure of my authority

1. **Standing memory for `developer-hub` sync.** Workspace memory holds a standing approval to sync that Application. This run's instruction says Argo syncs need explicit approval, one at a time, and that later, narrower instruction wins. No step needed it.
2. **Reading retained topic records.** I read the two records with a group-less console consumer, so nothing was committed, and printed them without `customerId`. Treated as read-only inspection.
3. **Checking the Git-declared database password.** I checked whether the public manifest's two values look like placeholders, printing only yes or no. I did not read the cluster Secret.
4. **Building `order-service` locally.** Built from `git archive origin/main` in the scratch directory, for the local saga. The order clone and its branches were not touched.
5. **`/retest` on my own GitOps PR.** A comment to rerun a check that failed on a PAC credential race.
6. **Pattern kill of test processes.** I tried `pkill -f` on `target/quarkus-app/quarkus-run.jar` to clear my own stray test processes. The permission layer denied it. Listing them showed five `order-service` processes, 5 to 7 hours old, matching the same pattern, which it would have killed. I killed only the two PIDs whose working directory was `inventory-service` and which started during my failed run.

7. **"Do what you think is best."** I read it as covering D-002, D-010 and D-011. I kept the admin routes closed, rather than create a Keycloak credential on a general delegation. The live order is a write to another service's data and shared topics, so the permission layer required an explicit approval, which I did not work around.
8. **Partial sync.** `box1-kafka` has no automated sync. I synced only the new KafkaTopic, with prune off, through the Application's operation field, after confirming it was the only resource out of sync.

## Did the order pilot's lessons prevent repeats?

| Order lesson | Applied here | Result |
|---|---|---|
| A ConfigMap literal change orphans a hashed name and fails promote (log 12) | Floor, read policy and JVM option are Deployment `env` entries | **Prevented.** Promote passed first time, and Argo stayed `Synced`. |
| Guava and base image CVEs fail the gate (`order-service#3`) | Found by diffing the scaffold in Phase 0; override applied | **Prevented.** The first gated release passed: scan exit 0, policy pass. |
| Template default `security-gates: disabled` (#42) | Set to `gate` in this repository | Applied |
| Read the working path of gate dependencies (log 14, 17) | This run's credential rule forbids direct probes. I used the pipeline's own runs: Order's two latest releases passed `security` with gate at 16:33 and 16:39 UTC. | **Partly.** That proves scan and SBOM, but those releases then failed at promote, for reasons not established. |
| Reviewers find defects tests miss (repairs 5 to 9) | Built in bounded fields, fixed DLQ headers, long DB retries, fail-fast publisher | **Partly.** Those classes did not recur. Reviewers still found new ones, including in the long-retry design itself. |
| Clock domains (repair 3) | Kept separate (D-009) | **Prevented.** No reviewer found a clock-domain defect. |
| Dead-letter topic must exist first | Separate PR and documented merge order | **Prevented.** Topic `Ready` before the service merged. Failure path still untested. |
| Save test keys (log 18) | The live order command recorded its key first | Not reached: the order was not created |
| Don't publish live weaknesses (ambiguity 8) | Pointers only in D-012 and the Security review | Applied |
| Laptop sleep during unattended runs | `caffeinate -ims` on every long run | **Did not prevent it.** The workstation slept from about 12:50 to 16:51 EST with no run in flight. The suite and saga reran on an awake machine afterwards. |
| One cause looks like many failures | Read causes before counting | **Repeated anyway,** with the leaked test process. Caught by reading the cause. |
| Stop timing: a stop blocks dependent work only | Now in the request | No ambiguity this time |

## Environment findings

- The workstation slept for about 4 hours, from 12:50 to 16:51 EST, despite `caffeinate -ims` for running jobs. `pmset` shows assertions held during runs. Why it slept between runs is not established.
- Five `quarkus-run.jar` processes are running with `order-service` as their working directory, 5 to 7 hours old at 12:00 EST. They look like leftovers from order-run test failures. Not touched.
- `box1-gitops` main received Keycloak changes during this run, including "Adding Keycloak authentication for RHDH", and the realm sync. They may affect D-010. Not reviewed.
- Order's latest releases fail at promote, and its promotion PR `box1-workloads-dev#56` is blocked by `box1-phase1-smoke`. The deployed Order is still `4ec33fb`. See `evidence/07-pre-deploy-recheck.txt`.

## Side effects outside the run state

- `git fetch --prune` in your `box1-docs` clone. Plain `git fetch` in the `box1-gitops`, `box1-ops-contracts`, `box1-workloads-dev`, `box1-templates`, `order-service` and `quarkus-reference` clones. Checkouts were not changed.
- New worktrees: `run12-docs`, `run12-contracts`, `run12-workloads`, `run12-gitops`. New clone: `inventory-service`.
- Pushed branches: `inventory-domain` (inventory-service), `inventory-service-v1` (box1-ops-contracts), `inventory-dlq-topic` (box1-gitops), `inventory-service-runtime-config` (box1-workloads-dev), and this run-state branch.
- Opened PRs, none merged: `inventory-service#1`, `box1-ops-contracts#5`, `box1-gitops#57`, `box1-workloads-dev#57`. One `/retest` comment on `box1-gitops#57`. CI runs those PRs triggered in `box1-ci`.
- With a concurrency limit of 1, my two first `box1-workloads-dev#57` runs queued behind Order's `#56`. All were cancelled together at 16:57 UTC by something outside this run.
- Local Podman: Testcontainers images, and named containers `run12-pg` and `run12-kafka`, each removed after its run. The order-service jar was built in the scratch directory.
- Reviewer subagents: the Operations pass downloaded the public base-image manifest and one layer to the scratch directory and deleted them. The Security pass disassembled local Maven jars into the scratch directory.
- With the user's approval: merged `box1-ops-contracts#5` (e278940), `box1-gitops#57` (2feea46), `box1-workloads-dev#57` (bf71c01), `inventory-service#1` (6b722a3). Synced one resource of `box1-kafka`, which created topic `box1.inventory.dlq.v1`. The release created and auto-merged `box1-workloads-dev#58`, applied Flyway V1 and V2 to the inventory database, created consumer group `inventory`, and uploaded one SBOM to RHTPA. A refresh annotation was set on two Argo Applications.
- The deployed service skipped the two retained events, as designed. No order was created, and nothing was produced to shared topics by this run.
