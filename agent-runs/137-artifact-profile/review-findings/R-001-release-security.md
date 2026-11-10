# R-001 Release and security review (fresh subagent, 2026-11-09)

Reviewer: a fresh general-purpose subagent given the two diffs, the prompt and the #136/#139 contracts (not the implementation reasoning). Reviewed box1-templates 2bd4c96 and box1-gitops 922b265. Same-model review; does not replace human PR review.

Result: no high or medium findings. Local tests re-run by the reviewer passed. `box1-quarkus-maven`, `quarkus-rest-service`, `rhel-image-vm`, `github-repository` unchanged.

## Release pass

| # | Sev | Finding | Disposition |
| --- | --- | --- | --- |
| R1 | low | Another reference to the bundle (FROM alias, mount) was only reported when the COPY count was wrong; with one COPY line it kept the old digest silently | **Fixed** box1-gitops 59e1ef0: any other reference fails; test added |
| R2 | low | Verify (outcome `current`) read the consumer at `main`, the task uses the default branch | **Fixed** box1-templates 6d4eef4; test uses a `trunk` default branch |
| R3 | low | Consumer params rendered unquoted in `.tekton/release.yaml` (YAML could read `true`/`null`/numbers) | **Fixed** 6d4eef4 (`dump`) |
| R4 | low | `consumerRepository == name` only caught at the platform phase | Accepted: fails before any build; JSON Schema cannot compare fields. Follow-up candidate |
| R5 | info | Same-digest rerun depends on Maven output reproducibility | Locally shown (two builds, same digest); cluster not observed |
| R6 | info | Consumer file mode forced to 100644 | Open (low impact for a Containerfile); follow-up |
| R7 | info | Onboarding run is outside PaC's concurrency queue; small race window | Accepted; plugin refuses to build if main moved, task re-checks |
| R8 | info | Registry acceptance of OCI manifest with `--preserve-digests`; RHACS on FROM-scratch | Not tested; live acceptance |

## Security pass

| # | Sev | Finding | Disposition |
| --- | --- | --- | --- |
| S1 | low | Onboarding token has write on the source as well as the consumer | Documented tradeoff (D-005); contained to platform steps, deleted after run |
| S2 | low | `bundle/<repo>` force-update without ownership check when no marked PR on the default base | **Fixed** 59e1ef0: PRs listed on any base, other base refused, leftover branch reused only if its tip is a bump commit; tests added |
| S3 | low/info | push step shared HOME/workspace with the `mvn` step (registries.conf/auth.json planting) | **Fixed** 59e1ef0: private HOME, REGISTRY_AUTH_FILE, CONTAINERS_REGISTRIES_CONF in /tmp; test asserts |
| S4 | info | PaC token scoping needs the consumer registered as a PaC Repository | **Documented** in GOLDEN-PATH (59e1ef0); `site-gateway-os` gets one from `rhel-image-vm` onboarding |
| S5 | info | Any box1-org repo except box1-gitops/box1-workloads-dev may be a consumer (e.g. box1-templates) | Open owner decision: deny more names? |
| S6 | info | Pre-existing: who can merge to main controls the release PipelineRun | Not widened by this change |
