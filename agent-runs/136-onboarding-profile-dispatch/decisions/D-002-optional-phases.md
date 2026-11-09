# D-002 How optional phases are expressed

**Decision.** A handler set to `null` declares the phase absent; every key must be present (contract test). Effects:

- `validateBundle: null` -> `provision` and `promote` skip; `platform`/`build` do not request or await the Application sync.
- `promotionUpdates: null` -> no promotion PR and no promotion sync.
- `buildSpec: null` -> no PipelineRun or credential; `build` saves `await buildResults(w, null)` as IMAGE_BUILT (vm-instance adopts approved digests this way).
- `buildSpec` and `buildResults` both null -> no build at all.
- `buildBarrier`, `platformChecks`, `verify: null` -> that wait is skipped.
- `sourceRepository: false` -> `box1:repository:ensure` is refused; `initialRecord` lets `provision` create the record.

A skipped phase still runs `checkpoint()` (recorded source revision and profile) and logs `state=skipped reason=...`.

**Why.** Explicit and testable (test-only profiles in `scripts/test-onboarding-profiles.cjs`); no `provision:false` flags parallel to handlers.

**Known limits (README):** Application name is fixed to `<name>`; promotion PRs only in `box1-workloads-dev`; catalog target fixed to `component:default/<name>` from the source repo; with no source repository the template must run catalog steps after `provision`. #137/#138 extend these through new handlers, not profile-name branches.
