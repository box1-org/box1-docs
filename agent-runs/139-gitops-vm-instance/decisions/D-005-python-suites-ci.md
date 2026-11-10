# D-005 Python suites stay out of CI in this change

**Decision:** do not wire `test-gitops-validate.py` / `test-gitops-promote.py` into a box1-gitops PR pipeline in #139. The coordinator files a follow-up issue; this run may not create issues.

**Reason:**
- The only PR pipeline, `.tekton/onboarding-plugin-guard.yaml`, deliberately runs a guard fetched from `main` against the PR tree, with `GITHUB_TOKEN` in its environment.
- Running the PR's own test files there would execute PR-supplied code next to a token.
- Doing it safely needs a new PipelineRun with two steps:
  1. a token step that downloads the PR tarball into an emptyDir;
  2. a token-free step that runs both suites with a pinned, sha256-checked kubectl (as the validator downloads it).
- It also needs a ServiceAccount decision (for example `ci-test`). That is a small but separate trust decision, and it would widen a PR whose merge already changes a required check.

**Proposed follow-up:** add `.tekton/task-contract-tests.yaml` (`on-event: pull_request`, paths `platform/pipelines/tasks/**`) with the two steps above. Acceptance: a PR breaking either suite gets a failing check.
