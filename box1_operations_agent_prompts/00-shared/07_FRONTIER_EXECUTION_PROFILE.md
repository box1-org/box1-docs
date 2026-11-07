# Frontier execution profile

Applies only when a run selects `frontier` from `manifest.json`. It changes **how** the agent executes a prompt, never **what** the prompt requires. Service and platform prompts stay the single source of requirements, and `00_AGENT_CONTRACT.md` immutable rules still apply in full.

**Mission:** own one bounded prompt from discovery through design, implementation, adversarial verification, GitOps delivery, live acceptance and evidence-backed handoff. Plan the internal work yourself. Stop only at a decision or authorization boundary.

More autonomy is not more scope. A frontier run still covers one service or platform prompt, plus only the test doubles, contracts, manifests and documentation it requires.

## Phases

Independent work may be reordered inside a phase. A phase is not complete until its exit criteria are met or its blocker is recorded.

| Phase | Output | Exit criteria |
|---|---|---|
| 0 Discovery | Baseline of repositories, branches, Golden Path patterns, GitOps layout, dependencies, CRD/operator versions, node resource pressure | Actual state recorded; conflicts and missing dependencies listed; nothing assumed from prompt text |
| 1 Design | Decision records, plan, requirement ledger, migration and rollout plan, assumptions and exclusions | Every behavior the prompt leaves implicit is decided and recorded before code depends on it |
| 2 Contracts | Changes to or consumption of `box1-ops-contracts` | Implementation target validates against shared contracts; no local copy of a shared schema |
| 3 Implementation | Code, migrations, tests, config, docs | Prompt behavior implemented; targeted tests pass |
| 4 Verification and repair | Fault scenarios, repairs | Prompt's failure modes exercised; in-scope failures repaired and retested |
| 5 Review | Findings per reviewer pass | Findings fixed or recorded with a next action |
| 6 GitOps delivery | Immutable image, promotion PR, Argo state | Digest and revision observed through the existing path |
| 7 Live acceptance and handoff | Runtime evidence, final handoff | Every requirement has a stated proof level; handoff complete |

## Authority

| Action | Authority |
|---|---|
| Read-only repository and cluster inspection | Allowed |
| Source edits, commits and pushes on a feature branch of the target service repo | Allowed |
| Local tests, including local fault injection with Testcontainers or Dev Services | Allowed |
| Opening a pull request in a service or contracts repository | Allowed |
| Opening a pull request in a GitOps repository | Allowed; the PR must state what merging it deploys |
| Creating a repository or running Golden Path onboarding | **Approval required.** Onboarding creates the repository, merges GitOps PRs and deploys |
| Merging to a service repository's `main` | **Approval required.** Merge starts the build and the dev promotion, which auto-merges after exact-head checks |
| Merging to a GitOps or shared contracts repository | **Approval required** |
| Shared infrastructure changes such as Kafka topics, RBAC or operators | **Approval required**, delivered as a GitOps PR |
| New secret, credential or permission | **Approval required**; provisioning is documented, values never recorded |
| Destructive migration or anything affecting shared persistent data | **Approval required** |
| Fault injection or data reset on the cluster | **Approval required**, and only in a named demo namespace per `06_RESOURCE_AND_SECURITY_BOUNDARIES.md` |
| Direct cluster mutation (`oc apply`, `oc patch`) as the deployment mechanism | **Prohibited** |

Approval covers the specific action requested. It does not carry over to later actions in the run.

## Stop conditions

Repair anything that is in scope and safe. Stop and report when:

- the actual repository or platform conflicts with the prompt;
- a required dependency or operator is unavailable;
- a breaking contract change is required;
- the next action needs approval under the table above;
- a requirement cannot be proven with available evidence;
- a product or ownership decision is required.

Context pressure is not a stop condition. Update the checkpoint, summarize, and continue. Retrieve files as needed rather than loading whole repositories.

## Parallelism

Read-only discovery, test design and review may run in parallel. Writes to the same source paths are serialized through one branch. GitOps writes are always serialized.

## Run state

Keep run state outside the service repository, in `box1-docs` under `agent-runs/<issue>-<short-topic>/`, on the run's own branch:

```text
run.json                 # issue, profile, repositories, current phase, current commits
requirements.yaml        # requirement ledger
checkpoint.md            # resumable state
decisions/               # one record per decision
evidence/                # redacted command output and observations
review-findings/         # one file per reviewer pass
```

When the run reaches its final phase, or stops to wait on the owner, open a `box1-docs` pull request that merges `agent-runs/<issue>-<short-topic>/` into `main`. Link the merged path from the achievement log, not the branch: run branches are deleted once merged. Later updates to a merged run go in a follow-up pull request.

Never put run state in `box1-gitops`. Only consumer-facing architecture, contracts and runbooks belong in a service repository. Redact everything in `evidence/`: no credentials, tokens, kubeconfigs or unredacted authentication logs.

`checkpoint.md` must let a fresh session resume without the conversation. It records the current phase, completed work, branch and commit, changed files, test results, evidence paths, open risks, blocked decisions and the **exact next action**. Update it at each phase exit and before any long-running step.

## Requirement ledger

Maintain the ledger while working; do not reconstruct it at the end. Derive IDs from the prompt's requirement IDs and acceptance criteria.

```yaml
- id: ORD-IDEMP-001
  description: Same idempotency key and payload returns one logical order
  status: live_verified
  implementation: [src/main/java/.../IdempotencyService.java]
  tests: [src/test/java/.../ConcurrentIdempotencyTest.java]
  commands: ["./mvnw test -Dtest=ConcurrentIdempotencyTest"]
  evidence: [evidence/test-concurrent-idempotency.txt]
  deployment: {image_digest: "sha256:...", gitops_commit: "..."}
  limitations: []
```

`status` is the highest level actually observed:

`proposed` → `implemented` → `locally_tested` → `ci_verified` → `deployed` → `live_verified`

`blocked` and `superseded` record a requirement that left this path, with the reason in `limitations`. "Done" is not a status. A requirement above `implemented` must name the command and evidence that prove it.

## Reviewer passes

Run each pass after implementation, in a fresh subagent or session given the diff, prompt and contracts rather than the implementation reasoning. Record findings even when there are none. These passes are same-model review and do not replace human PR review or the existing CI gates.

- **Architecture:** service owns its state; no cross-service table reads; explicit transitions; no accidental distributed transaction.
- **Persistence:** unique constraints, concurrency, transaction boundaries, indexes, migration reruns and rollback.
- **Messaging:** outbox written in the business transaction; published only after broker confirmation; restart-safe claiming; bounded retries; harmless duplicates; recoverable poison events.
- **Security:** no secrets or unneeded customer data in source, logs, events or fixtures; internal endpoints protected; declarative secret references.
- **Operations:** readiness behavior, resource requests that fit the single node, measurable lag, trace and log correlation, runbook recovery and replay.
- **Release:** digest matches the GitOps promotion; Argo reports the expected revision; running pod uses that digest; endpoint and OpenAPI examples work.

## Completion

The model's prose is not the completion signal. Before reporting completion, re-derive the result from primary sources: test result files, `git status` and diff, image digest, GitOps commit, Argo status and endpoint responses. Then confirm every ledger entry agrees with them.

**No automated runner enforces this profile yet.** The agent performs this check and a human reviews it. Source changes and generated manifests alone never count as completion; requirements not at `live_verified` are reported at the level they reached.

End with `05_HANDOFF_TEMPLATE.md`, including its run state block.
