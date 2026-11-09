# Checkpoint: box1-docs#136 onboarding profile dispatch

**Phase:** 5 Review complete. Stopped at the authorization boundary before phase 6 (merge, tag release, pin PR, Hub sync) and 7 (live regression onboardings). Updated 2026-11-08 23:35 America/New_York.

## Done
- Discovery (evidence/01): box1-templates main 5663eb3, line refs confirmed; deployed plugin 1.2.0 `sha256:98506a25…0bb8b` (rev 8537ec1) in box1-gitops and the running Hub Pod; newest tag onboarding-plugin-v1.2.0; no active onboarding (all leases released, all records COMPLETE).
- box1-templates branch `golden-path/136-profile-dispatch`, PR [#33](https://github.com/box1-org/box1-templates/pull/33), head `d8e8533`:
  1. `b0e65d8` characterisation test + fixture, green on old code;
  2. `ca3bf00` dispatch-table refactor + three coupled VM tests rewritten (reasons in commit message);
  3. `5491221` test-only profile tests (`scripts/test-onboarding-profiles.cjs`);
  4. `ffeb714` README "Adding an onboarding profile (1.3.0)", version 1.3.0;
  5. `d8e8533` review-pass-1 fixes (`scripts/test-onboarding-sync-equivalence.cjs`, contract tightening, README limits).
- Tests: local and CI 75/75 + 26/26; characterisation test/fixture unchanged since b0e65d8 (evidence/02, 03).
- Review pass 1 (review-findings/01): no service/VM behaviour change; findings fixed or documented.

## Changed files (box1-templates)
`plugins/box1-onboarding/{workflow.cjs,index.cjs,README.md,package.json}`, `package.json` (test:onboarding list), `scripts/test-onboarding-vm.cjs`, `scripts/test-onboarding-oci.mjs`, new `scripts/test-onboarding-{characterisation,profiles,sync-equivalence}.cjs`, `scripts/fixtures/onboarding-profiles-characterisation.json`.

## Open risks
- Live behaviour on the new digest not established until regression onboardings run.
- `UPDATE_CHARACTERISATION=1` can regenerate the fixture; a fixture diff in a PR must be treated as a behaviour change.
- #137/#138 will need new handlers for the README-listed limits.

## Exact next action (user)
1. Review and merge box1-templates#33.
2. `git tag onboarding-plugin-v1.3.0 <merge-sha>` on main and push the tag; approve the release PipelineRun; record its name and the published digest (`npm run inspect:onboarding-oci`).
3. Merge the box1-gitops pin PR opened by the release (rollback digest in its body = 1.2.0 above).
4. Re-check no active onboarding (`oc -n rhdh get leases,configmaps | grep box1-onboard-`, all records COMPLETE/FAILED), then sync Argo `developer-hub`; confirm Pod annotation `box1.org/onboarding-plugin-digest` equals the new digest.
5. Approve and run regression onboardings `regress136-svc` (quarkus-rest-service) and `regress136-vm` (rhel-image-vm); record task IDs, status records, PRs, verify outputs; decommission per runbooks/service-decommission.md.
6. Then tick #136 items and unblock #137/#138 (handler interface: decisions/D-001).
