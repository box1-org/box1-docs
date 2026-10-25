# Platform 04 — TSSC, signing, attestations and admission


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** CICD-01–07; DEMO-B1/B2; NFR-08

**Dependencies:** Already validated Developer Hub Quarkus Golden Path, existing Pipelines as Code and Argo GitOps path.

## Mission

Extend the **existing functioning** software factory with trusted-supply-chain evidence. Do **not** reinstall pipelines, create a second GitHub App, replace a working Tekton release or regress SHA/digest promotion. This workstream is an incremental security-enhancement demo.

## Implementation scope and guardrails

- Baseline existing chain by inspecting `box1-org/quarkus-reference`, `box1-org/box1-templates`, Pipelines as Code config, manifest generation, image build/publish, GitOps promotion PR and Argo CD reconciliation. Preserve exact-head guard and digest deployment semantics.
- Add/verify SBOM production (CycloneDX/SPDX or supported format), vulnerability results, immutable SHA digest, image signature/attestation/provenance suitable for existing registry trust model; document cryptographic verification without assuming a cluster key-management service already exists.
- Map each result to source commit, build run and deployed digest. Surface evidence links in Developer Hub and optionally the operator/developer UI.
- Define an admission/promotion policy with fail-closed behavior for intentionally unsigned image or known test policy violation; select supported admission integration only after validating operator availability. It must not block unrelated cluster workloads.
- Controlled negative test: create a policy-violating candidate in an isolated PR/branch or test namespace, show explicit rejection reason and no protected deploy; then repair and prove signed digest deploys through GitOps.
- Update Golden Path templates only through isolated changes and acceptance tests. Do not let each application prompt independently add bespoke security steps or disable existing checks.
- Produce a component-level software bill of materials and platform operator version bill of materials; explain prerelease compatibility limitations.

## Verifiable acceptance evidence

- Existing Quarkus reference PR/merge workflow continues to pass after enhancements.
- Deliberately untrusted artifact is rejected with human-readable report and machine-verifiable evidence.
- Fixed artifact maps source SHA → tests → SBOM → signature/attestation → image digest → GitOps commit → observed Argo revision; only report links actually obtained.
- Rollback uses previous immutable digest; no `latest` deployment or manual Tekton `oc apply` path appears.

## Nominal 64K-context implementation slices

1. Record current golden path and threat model; no changes yet.
2. Generate/verify SBOM and provenance with existing build.
3. Sign/verify digest and wire supported policy check.
4. Negative gate scenario then successful fix/promotion.
5. Catalog evidence, reproducible runbook and regression tests.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
