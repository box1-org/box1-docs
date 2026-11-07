# D-002 CI, security gates and pinned artifact for a Python repository

**Status:** PR opened at the user's request: [box1-gitops#61](https://github.com/box1-org/box1-gitops/pull/61) (not merged; `pipelines-ci` has no automated sync, so merging deploys nothing until a sync).

**Finding:** no Python CI path, no GitHub Actions anywhere in the org, no non-container artifact store. `box1-security-gates` only scans image digests. `rhel-image-poc` shows the pattern: inline `.tekton/` tasks, `box1-ci` registry project, Repository CR + SAs in a `box1-gitops` PR (#58, open).

**Decision (proposed):** Pipelines as Code with inline tasks in the ERP repo:
- PR pipeline: ruff, the unit/fixture test suite (container-free subset), `python -m build`.
- Release pipeline: build the wheel, record its sha256, package wheel + systemd units + `SHA256SUMS` as a `FROM scratch` OCI image pushed to `box1-ci/box1-ops-erp-simulator@sha256:…`, then `box1-security-gates` in observe mode.
- #25's bootc Containerfile consumes it with `COPY --from=<registry>/box1-ci/box1-ops-erp-simulator@sha256:<digest>`.

**Needs approval:** a `box1-gitops` PR for the PaC `Repository` CR and CI service accounts (no privileged SCC). This run will not open it without approval because the user restricted CI setup in shared repositories.

**Rejected:** GitHub Actions (first in the org, bypasses RHTPA/ACS/Chains, would publish outside the platform); a shared `box1-python` Task (more shared-repo change than one service justifies; follow-up once a second Python repo exists).

**Consequence:** until approved, the ledger's best level for test requirements is `locally_tested`, and VM-03 delivery (Phase 6) is blocked.

**Drafted (not run):** `.tekton/pull-request.yaml` (SA `ci-test`, image `ubi10/python-312-minimal` pinned by digest) and `.tekton/release.yaml` (SA `ci-erp-release`: push to `box1-ci/box1-ops-erp-simulator`, then `box1-security-gates` with the same parameters as rhel-image-poc, `enforcement: observe`). The box1-gitops change would add the PaC `Repository` CR for `box1-org/box1-ops-erp-simulator`, the `ci-erp-release` service account with push rights to `box1-ci/box1-ops-erp-simulator` only, and nothing privileged. The release's unprivileged buildah (vfs, chroot isolation) step is unverified.

**Changed before opening the PR (after re-reading rhel-image-poc):** the release no longer uses buildah. `scripts/make-oci-layout.py` builds a reproducible one-layer OCI layout (same digest on two builds; `skopeo inspect`/`copy` read it) and `ubi9/skopeo` (pinned) pushes it with the service-account token, trusting the service CA. Both pipelines extract tarballs with Python because the pinned UBI 10 Python image has no `tar` or `gzip` (checked). Push rights are a Role on `imagestreams/layers` for the one ImageStream, which the PR declares; unverified until the first release, fallback `system:image-builder`.
