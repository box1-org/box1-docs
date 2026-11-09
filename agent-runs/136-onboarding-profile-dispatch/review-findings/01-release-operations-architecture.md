# Review pass 1: release, operations, architecture (fresh subagent)

Reviewer input: the #136 prompt, the #137/#138 prompts, the diff 5663eb3..ffeb714 and the checked-out repo; no implementation reasoning. Same-model review; does not replace human PR review or CI.

**Verdict:** no behavioural difference for `service` or `virtual-machine`; no blocker. Reviewer verified moved bodies line by line, call order (buildResults before Secret cleanup, requireImageDigest before waits, platformComplete before promotion edits), record/marker key order, catalog results and messages, `profileInputSchema()` equal to the old literal, records readable by 1.2.0, characterisation test unchanged and passing on the b0e65d8 tree, full suite green. Release: version complete, tag pipeline and smoke load unaffected.

| # | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| 1 | major (test gap) | Removing `awaitServiceSync` from `completePlatform` was not detected: fixture presets `applicationsSyncedAt` | Fixed d8e8533: `scripts/test-onboarding-sync-equivalence.cjs` (passes on 5663eb3 and head) |
| 2 | minor (test gap) | Secret cleanup ordering on rejected build results not observed; `UPDATE_CHARACTERISATION` rewrites the fixture before comparing | Ordering fixed in same file. Update switch left as is (editing the characterisation test after b0e65d8 is disallowed by the prompt); fixture changes are visible in review via git diff. Follow-up: refuse the switch when `CI` is set |
| 3 | major (contract, #138) | No-source-repo profile: catalog:submit before provision would create an incomplete record; catalog target hard-coded | Documented in README known limits and D-002/D-003; #138 to add a catalog handler or order steps after provision |
| 4 | major (contract, #137) | Non-null `validateBundle` assumes an Application named `<name>`; consumer-PR promote does not fit `promotionUpdates` | Documented in README known limits and D-002; #137 adds handlers (e.g. application name) |
| 5 | minor | "build done" keyed on `imageDigest` | Contract now requires `imageDigest` in buildResults (d8e8533) |
| 6 | minor | `buildSpec` without `buildResults` would crash after the PipelineRun | Contract test asserts it (d8e8533) |
| 7 | nit | README/contract inconsistencies (commitMessage null, `w` members) | Fixed d8e8533. Skip reasons/PR text saying "service" left unchanged (byte-identical PR text for existing profiles) |
| 8 | nit | Unknown recorded profile gives "Unsupported onboarding profile" in registerCatalog | Accepted; harmless |
