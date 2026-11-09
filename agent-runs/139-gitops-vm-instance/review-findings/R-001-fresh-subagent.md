# R-001 Fresh-subagent review (same model), 2026-11-08

**Reviewer input:** the diff `main...fade118` on `box1-gitops` `golden-path/139-vm-instance-validate-promote`, the #139 prompt, and the #140 and #137 prompt sections. It did not see the implementation reasoning.

**Passes run:** correctness/regression, requirements coverage, security (adversarial fixtures in `../evidence/review-fixtures/`), and operations/release.

**Reviewer disclosure:** it ran `kubectl create --dry-run=client -f` on the two Task files to check that the YAML parses. That client-side dry run may make a read-only discovery call to the kubeconfig's cluster. Nothing was created, and no other cluster calls were made. Recorded because this run's authority forbade mutating commands. A client dry run does not mutate, but it was not needed: the `TaskManifestsRender` test covers YAML validity.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | should-fix (high for ci/) | `pipelinerun_provenance` and the token-scope checks matched any 4-space key under `spec`. A decoy `git_provider.*` key satisfied them while `settings` held `source` or `box1-workloads-dev`. | **Fixed in `147145f`.** Values are read from `spec.settings` only, and the `spec` and `settings` keys are allowlisted. Tests: `test_repository_settings_are_read_from_settings_only`, `test_repository_spec_and_settings_keys_are_allowlisted`. |
| 2 | should-fix | Repository `spec.params[].secret_ref` and `spec.git_provider` (other host, Secret) passed. | **Fixed in `147145f`** by the same `spec` key allowlist. |
| 3 | should-fix | The ConfigMap check read only key names. `gateway.yaml: \| admin_password: …`, `PASSWORD=…` and `kubeconfig` all passed. | **Fixed in `147145f`.** Added the `EMBEDDED_CREDENTIAL` value regex and the word `kubeconfig`. Test: `test_site_configmap_values_must_not_embed_credentials`. |
| 4 | nit | Role wildcard detection matched a literal `*` only (`*/status` passed). `pods/exec`, `services/proxy` and similar passed with `resourceNames`. | **Fixed in `147145f`.** Any `*` is rejected, and the `exec`/`attach`/`portforward`/`proxy`/`token` subresources are rejected. Test: `test_role_resources_exclude_wildcard_and_proxy_subresources`. A full resource allowlist was not adopted, because #137's observer needs are not final. |
| 5 | should-fix | Day 2 does not swap the DataVolume digest, overriding an owner decision. | **Recorded** as D-006 and flagged in the PR body for owner sign-off. Not changed. |
| 6 | should-fix | CI wiring for the suites was neither proposed nor filed. | **Recorded** as D-005 with a proposed design. Documented in GOLDEN-PATH.md. The coordinator files the backlog issue, since this run may not create issues. |

**No problem found:**
- service and virtual-machine behaviour preserved;
- PR body byte-identical for old profiles;
- all ten prompt verification scenarios covered;
- cloud-init inline and secret-render bypasses, quoted values, `List` wrapping and Group subjects all rejected;
- Tekton param plumbing.

**After the fixes:** validate ran 68 tests, OK; promote ran 31, OK (Python 3.11 and 3.9). Old and new validators are identical on 60 `box1-workloads-dev` revisions plus PR #126.
