# Checkpoint: box1-docs#18 operator console (frontier)

**Current phase:** 1 Design is complete, pending user decisions O-1 to O-8 (none block Phase 3 code). **Next: Phase 2/3.**
**Updated:** 2026-11-05 ~23:05 EST.

## Done
- Phase 0 discovery: `evidence/00-discovery.md`.
- The front-end build is proven in the real PR pipeline: `evidence/01-frontend-build-probe.md`, PR operations-console#1 (draft probe, `ae245e7`), PipelineRun `operations-console-validate-zqk5s`.
- Phase 1 design: `decisions/D-001`…`D-015`, `open-decisions.md`, ledger `requirements.yaml` (36 entries).

## Branches and worktrees
- box1-docs `agent-run/18-operator-console`, worktree `/Users/mike/Documents/ChatGPT/box1/run18-docs`.
- operations-console clone `/Users/mike/Documents/ChatGPT/box1/run18-operations-console`, branch `run18-frontend-build-probe` (`ae245e7`). The implementation branch `issue-18-console` is to be cut from it.

## Exact next action
Cut `issue-18-console` from the probe branch. Write `META-INF/openapi.yaml` (D-006), the backend (D-003/D-007/D-008), the front end (D-001/D-014), then tests (D-015).

## Open risks
- G-1, G-2 and G-3: see `open-decisions.md`.
- Build egress to nodejs.org and npmjs.org is observed, not guaranteed.
