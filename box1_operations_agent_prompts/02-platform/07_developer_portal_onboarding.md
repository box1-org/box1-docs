# Platform 07 — Developer Hub service onboarding and catalog UX


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** CICD-01/03/06/07; PLT-01/02

**Dependencies:** Existing `box1-org/box1-templates` golden-path workflow and GitOps onboarding automation.

## Mission

Onboard the new box1 Operations services by reusing the **already completed and end-to-end validated** `Create Quarkus Service` template. The task is to make the new services discoverable and reproducible, not to create another platform installation.

## Implementation scope and guardrails

- Inspect Developer Hub template, real catalog conventions and generated repository pattern; verify which new services already exist before invoking templating.
- For each Quarkus service generated: Java 21, REST/health/OpenAPI/Micrometer, basic tests, existing Pipelines as Code setup, app metadata owner, README and GitOps onboarding PR to `<service>-dev` according to live convention. Preserve `/api/info` image SHA exposure.
- Register all service components and relations (consumes API, produces events, owns database, exposed by BFF), system grouping `box1-operations`, environments and API descriptors.
- Ensure Quarkus archetype works from Hub API even if browser sign-in is temporarily limited, but do not bypass OAuth/authentication by exposing an unauthenticated creation API.
- For non-Java services (console and optional model tooling) define a separate, reviewed compatible template rather than claiming Quarkus template generates React automatically.
- Validate GitHub App and secret setup by reading existing versioned manifests; do not request duplicate App installation.
- Generate reproducible onboarding checklist with exactly who reviews a GitOps PR, where a pipeline test is visible, and what proves digest rollout/rollback.

## Verifiable acceptance evidence

- At least two **new** box1 Operations services can be scaffolded, built, promoted and appear in Developer Hub with correct catalog metadata.
- No existing `orders-service`, reference repo or current namespace is unintentionally changed.
- CI/Argo shows digest/SHA contract and `/api/info` reflects the deployed commit.
- Generated docs include requirements mapping, OpenAPI link, owner, runbook and observability pointers.

## Nominal 64K-context implementation slices

1. Read current template/catalog and identify gaps with service specification.
2. Onboard first new Quarkus service and verify actual CI/GitOps behavior.
3. Catalog API and component relationships.
4. Onboard second service, validate no template regressions and document handoff.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
