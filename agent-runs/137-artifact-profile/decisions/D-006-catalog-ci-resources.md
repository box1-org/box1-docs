# D-006 Catalog type and ci/ resource list

**Catalog.** Component `spec.type: library`; annotations `github.com/project-slug`, `backstage.io/techdocs-ref: dir:.`, `backstage.io/source-location`, `janus-idp.io/tekton`, `box1.org/template-version`, `box1.org/bundle-image`, `box1.org/bundle-consumer`; **no** `backstage.io/kubernetes-id`, `argocd/*`. Template `spec.type: library`.

**ci/<repo>/ resources** (all `box1-ci`): Repository `<repo>` (url, `concurrency_limit: 1`, `settings.pipelinerun_provenance: default_branch`, `github_app_token_scope_repos: [box1-org/<consumer>]`); ServiceAccount `<repo>-release`; ImageStream `<repo>-bundle`; Role `<repo>-bundle-push` (`get`, `update` on `imagestreams/layers`, resourceNames `<repo>-bundle`); RoleBinding `<repo>-bundle-push` → `<repo>-release`. Plus `applications/<repo>-ci.yaml` (Argo `default` project, `ci/<repo>` on main, destination `box1-ci`, automated selfHeal, no prune). Passes #139's `check_ci` (evidence/gitops-tests.txt).

**Deviation.** The prompt lists "observer Roles"; none are generated because no task in the artifact release observes a workload, and RBAC outside box1-ci cannot live in ci/. Owner to confirm.

**Cluster RBAC outside ci/:** Hub Role `developer-hub-onboarding-build` gains `get imagestreams` in box1-ci (box1-gitops#133). Argo's controller can create all ci/ kinds in box1-ci (`oc auth can-i --as` checks, 2026-11-08). PR runs use the existing `ci-test`; `system:image-pullers` already lets every box1-ci SA pull (gate scan).
