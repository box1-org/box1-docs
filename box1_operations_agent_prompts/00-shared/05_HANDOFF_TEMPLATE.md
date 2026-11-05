# Agent handoff — fill this out at the end of every session

## Work completed
- Service / platform workstream:
- Slice / requirements:
- Repository and branch:
- Changed paths:
- PR / commit (if actually created):

## Tests and deployment proof
- Exact commands and observed results:
- CI status (if accessible):
- GitOps PR and deployed image digest (if actually observed):
- Routes / endpoints verified (if any):

## Contract state
- OpenAPI / event schemas changed:
- Database migrations and forward compatibility:
- Consumer compatibility / pending follow-up:

## Operations and safety
- Secrets externalized / auth boundaries:
- Telemetry evidence:
- Resource settings:
- Known risks and recovery/rollback:

## Next agent session
- Next smallest slice:
- Exact files to read (not whole repo):
- Blockers and required user decisions:
- Context budget warning if near the 64K limit (`qwen-64k` only):

## Run state (`frontier` only)

```yaml
profile: frontier
issue:
current_phase:
repositories:
  - name:
    branch:
    commit:
run_state_path:
requirements:          # counts by ledger status
  proposed: 0
  implemented: 0
  locally_tested: 0
  ci_verified: 0
  deployed: 0
  live_verified: 0
  blocked: 0
  superseded: 0
image_digest:
gitops_commit:
review_passes_completed: []
open_decisions: []
rollback_state:
next_action:
```
