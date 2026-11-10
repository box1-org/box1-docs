# Handoff: box1-docs#136

## Work completed
- Platform workstream: Developer Hub onboarding plugin, profile dispatch table (1.3.0).
- Repository and branch: box1-org/box1-templates `golden-path/136-profile-dispatch`, head `d8e853318046ab0544fac95330d20d525c964e9b`; PR https://github.com/box1-org/box1-templates/pull/33 (open, not merged).
- Characterisation test: `scripts/test-onboarding-characterisation.cjs` + `scripts/fixtures/onboarding-profiles-characterisation.json` (commit b0e65d8, unchanged since).
- Handler interface for #137/#138: decisions/D-001, `workflow.cjs` L20-75 at d8e8533, README "Adding an onboarding profile (1.3.0)".

## Tests and deployment proof
- `npm ci && npm run validate && npm run test:onboarding && npm run test:onboarding-oci`: local 75/75, 26/26; CI box1-onboarding-plugin-pr-65wx6 Succeeded on d8e8533 with the same counts.
- Plugin version 1.3.0; digest: none (not released). Pin PR: none. Regression task IDs: none. Decommission state: nothing created.
- Rollback digest: `sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b` (1.2.0, currently deployed).

## Contract state
- Scaffolder action schemas unchanged (characterisation actionSchemas). Records/markers unchanged for service and VM; 1.2.0 can read 1.3.0 records.

## Operations and safety
- No cluster mutations, no merges, no tags, no secrets. Recovery: the release is not yet made; after release, rollback is reverting the pin to the 1.2.0 digest and syncing developer-hub.

## Next agent session
- Next slice: user release steps in checkpoint.md, then live regression (needs approval).
- Blockers / user decisions: merge #33; tag; approve onboarding of regress136-svc / regress136-vm.

## Run state
```yaml
profile: frontier
issue: box1-org/box1-docs#136
current_phase: 5 (stopped before 6 at authorization boundary)
repositories:
  - name: box1-org/box1-templates
    branch: golden-path/136-profile-dispatch
    commit: d8e853318046ab0544fac95330d20d525c964e9b
  - name: box1-org/box1-docs
    branch: agent-run/136-onboarding-profile-dispatch
    commit: (this PR)
run_state_path: agent-runs/136-onboarding-profile-dispatch/
requirements:
  proposed: 1
  implemented: 1
  locally_tested: 0
  ci_verified: 8
  deployed: 0
  live_verified: 0
  blocked: 0
  superseded: 0
image_digest: null
gitops_commit: null
review_passes_completed: [release+operations+architecture]
open_decisions: [approve live regression onboardings]
rollback_state: 1.2.0 sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b still deployed
next_action: user merges box1-templates#33 and pushes tag onboarding-plugin-v1.3.0
```
