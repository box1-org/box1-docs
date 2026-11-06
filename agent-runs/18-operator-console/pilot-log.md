# Frontier profile pilot log: box1-docs#18

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|

## Repairs

Found during Phase 0 (probe), fixed and retested:

1. **React 19 has no global `JSX` namespace.** The probe's `App(): JSX.Element` failed `tsc --noEmit` locally. Changed to `React.JSX.Element`. This shows the typecheck gate works inside the Maven build.

## Profile ambiguity and friction

1. **The prompt's discovery list was partly stale on arrival.** It says the operator did not create `spec.roles` (#59), but #59 was closed as not-a-defect 23 minutes before this run started. It also proposes `box1-ops-console`, while the onboarded repository is `operations-console`. Both were checked rather than assumed.

## Places I was unsure of my authority

## Did earlier pilots' lessons prevent repeats?

| Earlier lesson | Applied here | Result |
|---|---|---|
| Check that a release-gate dependency actually works, not just that a pod runs (runs 11, 13) | Proved the Node build in a real PR pipeline before writing the front end | **Prevented.** Proven at 1m17s, before any front-end work |
| PaC takes pipeline definitions from `main` (run 14) | The probe used the template's unchanged `.tekton/`, so its result carries to later PRs | Applied |
| Check host and Podman VM clocks (runs 11, 13) | Checked at 22:49:40 EST: in agreement | Applied |
| Name containers `runNN-*` and never blanket-remove (runs 11, 13) | Clone named `run18-operations-console`; no containers yet | Applied; not yet exercised |

## Environment findings

- 22:49 EST: host and Podman VM clocks agreed.
- The `legacy-erp` VMI restarted at about 22:45 EST. Another run appears active in `legacy-erp-dev`, and this run did not touch it.

## Building a front end on a Java Golden Path

- The Golden Path task has no Node, but it does have unrestricted egress. A Maven-driven Node install worked first time in CI.
- `frontend-maven-plugin` does not verify the Node archive. Pairing it with `download-maven-plugin` (SHA-256) and a `file://` download root gives the same supply-chain posture the platform applies to Maven itself.
- Generating the lockfile needed the pinned Node: the workstation had Node 25, and `engine-strict` refused it. TypeScript 7 and rolldown ship native binaries as optional dependencies, and the macOS-generated lockfile included the linux-x64 entries.

## Consuming other runs' APIs

- Each upstream accepts a different token shape: no auth (order), `aud` only (inventory, adapter), `aud` plus `azp` (asset).
- The order → fulfillment link exists only as an internal naming convention in order-service.
- The fulfillment adapter has no contract in `box1-ops-contracts`, only its served OpenAPI.

## Side effects outside the run state

- Clone `/Users/mike/Documents/ChatGPT/box1/run18-operations-console`, plus worktree `run18-docs` of box1-docs.
- Pushed branch `run18-frontend-build-probe` and opened draft PR box1-org/operations-console#1 (`ae245e7`). That PR triggered PipelineRun `box1-ci/operations-console-validate-zqk5s`.
