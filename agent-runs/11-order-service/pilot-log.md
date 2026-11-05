# Frontier profile pilot log: box1-docs#11

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 1 | 2026-11-05 02:40 EST | 0 exit | Repository conflicts with prompt; product or ownership decision required | `order-service` exists where the prompt proposes `box1-ops-order`. See `decisions/D-001` to `D-005`. |

## Repairs

None in product code. One harness adjustment: the scaffold's `verify` failed locally because Testcontainers found no Docker socket. Pointing `DOCKER_HOST` at the Podman socket and setting `TESTCONTAINERS_RYUK_DISABLED=true` made it pass with no source change. This applies to this workstation only. Why CI passes without that setting was not established.

## Profile ambiguity and friction

1. **Does a stop halt all work, or only dependent work?** The profile says "stop and report". The first condition fired while contract fixes and design were still possible. I stopped at the Phase 0 exit, because the open decisions feed into the design, and so the report could carry them all at once. A rule either way would help.
2. **Phase 0 "conflicts listed" versus "stop when conflicts exist".** Discovery expects to find conflicts and "resolved in design" covers contract differences, while the stop list covers repository and platform conflicts. The boundary between a conflict to resolve and one to stop on is a judgment call.
3. **"GitOps repository" is undefined.** The conventions name `box1-gitops`, but workloads live in `box1-workloads-dev`.
4. **Stale prompt premises.** `orders-service` is retired, yet Phase 6 still requires showing it is unchanged. There is no status for "the requirement's premise no longer exists" except `blocked` or `superseded`.
5. **Undefined requirement IDs.** The profile derives ledger IDs from the prompt's requirement IDs, but FR-01, DAT-03 and OBS-01 are not defined on `box1-docs` main.
6. **The ledger's `ci_verified` level assumes CI can run the tests.** The `box1-quarkus-maven` task has no sidecars, so container-backed tests may be limited to `locally_tested` unless the design uses an embedded database. Whether containers can run in that step was not tested.
7. **No named demo namespace.** Cluster fault injection is allowed only in one, and none is named.
8. **Run state lives in a public repository, and the profile does not say so.** `box1-docs` is public. The profile bans credentials in `evidence/`, but says nothing about a live weakness found during discovery. I nearly published one. I withheld the specifics from the run state and reported them directly. The profile should say where such findings go.

## Places I was unsure of my authority

1. **Pushing to `order-service`.** "The service repository" could cover it, since it is the only order service that exists. It is not the repo the prompt names, so I did not push. See D-001.
2. **`box1-workloads-dev`.** It is not in the standing permissions, though the profile would allow a PR. I did not assume it. See D-002.
3. **Reading a Secret for a comparison.** I treated this as read-only inspection. The values were compared in the shell and only yes or no was output. Flagged so you can say if you want that handled differently.
4. **What to publish.** The standing permission covers pushing run state to `box1-docs`, but it was written without saying the repository is public, so I narrowed what I pushed for D-005.

## Side effects outside the run state

- `git fetch --prune` in your `box1-docs` clone removed stale remote-tracking refs for deleted branches. Your checkout, branch and untracked file were not changed.
- `git fetch` ran in the `box1-gitops`, `box1-ops-contracts`, `box1-templates`, `box1-workloads-dev` and `quarkus-reference` clones.
- New worktree: `box1-docs-agent-run-11`, on branch `agent-run/11-order-service`.
- Local Podman pulled `postgres:15-alpine` and the Kafka Dev Services image. A pull of the RHEL PostgreSQL image failed for lack of registry login.
- The cluster and all other repositories were read only.
