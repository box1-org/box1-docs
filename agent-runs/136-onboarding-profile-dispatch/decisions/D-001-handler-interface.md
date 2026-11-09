# D-001 Handler interface and names

**Decision.** `PROFILES` in `plugins/box1-onboarding/workflow.cjs` (box1-templates, comment block and table L20-75 at d8e8533) is the dispatch table. Each entry declares all of:

| Key | Shape |
| --- | --- |
| `templateVersion` | string |
| `commitMessage` | string, or null only with `sourceRepository:false` |
| `sourceRepository` | optional boolean, default true |
| `initialRecord(w)` | optional async -> record fields incl. `sourceRevision`; only for `sourceRepository:false` |
| `recordFields(w)` / `markerFields(w)` | -> object (service `{}`, others `{profile: w.profile}`) |
| `validateBundle(files, name)` | -> files, or null |
| `buildBarrier(w)` | async, or null |
| `platformChecks(w)` | -> `{condition: async () => true or 'pending reason'}`, or null |
| `buildSpec(w, secretName)` | -> PipelineRun spec, or null |
| `buildResults(w, run)` | -> IMAGE_BUILT fields incl. `imageDigest`; `run` null without buildSpec; required with buildSpec |
| `promotionUpdates(w, files)` | async -> promotion PR files, or null |
| `verify(w)` | async, or null |
| `catalogComplete(data)` | -> boolean |

Handlers are plain functions taking the Workflow `w` (not methods), so a new profile adds functions next to its entry and never edits Workflow methods. The `w` members a handler may use are listed in the contract comment and the README.

**Why.** Keeps every profile difference in one place; the service and VM handlers are the previous code moved verbatim (`this` -> `w`), which the characterisation test proves.

**Not taken.** Nested `if (profile === ...)` branches (prompt). Handler methods on Workflow subclasses (would make the table indirect and the test-only profile harder).
