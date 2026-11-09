# D-005 Profile `artifact`, two generic hooks, plugin 1.4.0

**Decision.** Plugin 1.4.0 adds the `artifact` table entry and two **optional** keys to the #136 contract (absent = 1.3.0 behaviour; `service` and `virtual-machine` do not declare them):

```js
gitopsApplication(w) -> string                       // Argo Application synced by platform/build/promotion; default w.name
buildCredential(w)   -> {repositories, permissions}  // GitHub App token request for the first build's Secret;
                                                     // default {repositories:[w.name], permissions:{contents:'read'}}
```

Workflow change: `applicationName()` (used by `requestServiceSync`, `awaitServiceSync`, `requestPromotionSync`) and `buildToken()` call them. No profile-name branch.

`artifact` handlers: `validateArtifactBundle`, `artifactBuildBarrier` (loads consumer, D-003; waits for `<repo>-release`, `<repo>-bundle-push` binding, ImageStream), `artifactPlatformChecks` (release identity, push Role/Binding, ImageStream, PaC Repository scoped to the consumer, `<repo>-ci` Synced), `artifactBuildSpec` (= release pipeline, as `<repo>-release`), `artifactBuildResults` (digest; gate must be `pass`; consumer outcome opened/updated/unchanged/current), `promotionUpdates: null`, `artifactVerify`, `artifactComplete`.

**Credential tradeoff.** `buildCredential` for `artifact` = `[source, consumer]` with `contents: write`, `pull_requests: write`; GitHub applies one permission set to all listed repos, so the source also gets write. Contained: the token is only in the platform-owned `fetch` and consumer `propose` steps (not the `mvn` step env), in a labelled Secret owned by the PipelineRun, deleted after the run, ≤1 h. Two tokens would need a second Secret lifecycle in the Workflow; not done.

**Characterisation.** Fixture unchanged. The profile enum is generated from the table, so the characterisation test now compares action schemas with the enum restricted to service/virtual-machine and asserts they stay first; the enum assertions in `test-onboarding-vm.cjs` and `test-onboarding-profiles.cjs` list `artifact`. This is a test change, recorded for the reviewer.

**Version.** 1.4.0 (package.json, OCI test fixture). For #138: build on `golden-path/137-artifact-profile`; the hooks above are the only interface change.
