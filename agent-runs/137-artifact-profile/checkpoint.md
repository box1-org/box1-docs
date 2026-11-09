# Checkpoint — box1-docs#137 (`artifact` profile, `quarkus-monorepo`)

Updated 2026-11-09 (America/New_York). Phase: **5 Review done; stopped at the approval boundary before 6 Delivery.**

## State
- box1-templates `golden-path/137-artifact-profile` @ 6d4eef4, PR #35, base `golden-path/136-profile-dispatch` (#33). Template 1.0.0, plugin 1.4.0.
- box1-gitops `golden-path/137-maven-bundle` @ 59e1ef0, PR #133, base `golden-path/139-vm-instance-validate-promote` (#132).
- Tests: templates validate PASS, test:onboarding 86/86, test:onboarding-oci 26/26; gitops test-maven-bundle 26 OK (Py 3.9, 3.11), test-gitops-validate 68 OK, test-gitops-promote OK; #139 check_ci PASS on rendered ci/ bundles; local multi-module `mvn verify` SUCCESS; bundle digest reproducible across two builds; consumer COPY + run OK.
- Review R-001 done; low findings fixed or recorded.

## Discovery facts (2026-11-08)
- #136 not released (box1-templates#33 open); #139 not merged (box1-gitops#132 open).
- `site-gateway`, `site-gateway-os`: do not exist (gh 404). `oc get ns site-gateway-dev` NotFound.
- GitHub Apps `box1-pipelines` and `box1-developer-hub`: installed on all org repos with contents and pull_requests write.
- `box1-builder`: no skopeo. Hub SA lacked `get imagestreams` in box1-ci (added in #133).
- Argo controller can create SA/Role/RoleBinding/ImageStream/Repository in box1-ci.

## Open decisions
- Accept omission of observer Roles in ci/ (D-006).
- Deny more consumer names (box1-templates, box1-docs, box1-*)? (R-001 S5)

## Exact next action (user)
1. Merge box1-gitops#132, wait ~10 s, merge #133; let the platform pipelines Application sync.
2. Merge box1-templates#33, wait ~10 s, merge #35; tag `onboarding-plugin-v1.4.0`, approve release, merge pin PR, check no active onboarding, sync developer-hub.
3. Create `site-gateway-os` (#126, from rhel-image-vm) with one `COPY --from=…/box1-ci/site-gateway-bundle@sha256:<64 hex> / <path>` line (a zero digest is fine as the starting pin).
4. Approve onboarding `site-gateway` from the Hub; then collect the five acceptance evidences on #137.
