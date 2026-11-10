# D-003 How the consumer is declared and stored

**Decision.**
- Template parameters `consumerRepository` (bare `box1-org` name, never `box1-gitops`/`box1-workloads-dev`) and `consumerPath` (relative, no `.`/`..` segments; default `Containerfile`).
- Source of truth for every release: `.tekton/release.yaml` PipelineRun params `consumer-repository`, `consumer-path` (rendered with `dump`).
- Write access: the PaC Repository `github_app_token_scope_repos` in `box1-workloads-dev/ci/<repo>/repository.yaml` lists exactly that consumer.
- Onboarding record: the plugin's build barrier reads `.tekton/release.yaml` at the recorded source revision, requires the consumer to equal the merged Repository scope, and stores `consumer: {repository, path}` (no new action inputs, so action schemas other than the profile enum are unchanged).
- Catalog annotation `box1.org/bundle-consumer` (informational).

Changing the consumer later means changing both the release params and the token scope (README of the generated repo says so).

**Not taken.** A new action input (would change every action schema), or reading the rendered workspace (not stable across resumes).
