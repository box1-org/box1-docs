# CI: implementation PR in the Golden Path pipeline

- PR: box1-org/operations-console#2, head `d007f00ddd7be5e58e9be233c893f4f8adbd9561`.
- PipelineRun `box1-ci/operations-console-validate-l6jv2` Succeeded in 1m39s (2026-11-05 ~23:35 EST), using the unchanged `box1-quarkus-maven` task.

```
[INFO] Installed node locally.
[INFO] added 72 packages in 4s
[INFO] > openapi-typescript ../resources/META-INF/openapi.yaml -o src/api/schema.d.ts
[INFO] vite v8.3.6 building client environment for production...
[INFO] ✓ built in 408ms
[INFO] Tests run: 45, Failures: 0, Errors: 0, Skipped: 0
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] You have 0 Checkstyle violations.
[INFO] BugInstance size is 0
[INFO] BUILD SUCCESS
```

Ledger entries proven by these Maven tests are `ci_verified`. Their browser parts (Playwright) remain local evidence, because the task has no browser.
