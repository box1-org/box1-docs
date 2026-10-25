# Repository and delivery conventions

## Known starting point

- GitHub org: `box1-org`.
- Working Golden Path components: `quarkus-reference` and `box1-templates` (Create Quarkus Service).
- GitOps repository previously discussed as `box1-gitops`; **inspect its real structure before writing or suggesting changes**.
- Existing end-to-end demo service `orders-service` must be preserved.
- CI contract already demonstrated: PR tests/checkstyle/SpotBugs/FindSecBugs; merge builds SHA-tagged Jib UBI image and generates GitOps promotion PR; dev PR auto-merge after exact-head checks; Argo CD deploys immutable digest and verifies rollout/public endpoint; digest-based GitOps rollback.
- Routes follow `https://<route>.apps.ocp.box1.org/` when public routes are appropriate, but **do not expose internal microservices simply to make demos easier**.

## Proposed service repositories (verify before creating)

`box1-org/box1-ops-order`, `box1-ops-inventory`, `box1-ops-fulfillment`, `box1-ops-telemetry`, `box1-ops-notification`, `box1-ops-bff`, `box1-ops-console`, `box1-ops-ai`, `box1-ops-erp-simulator`, `box1-ops-scenario-control`, plus shared `box1-ops-contracts`.

For Quarkus: use Developer Hub Golden Path, keep `/q/health/live`, `/q/health/ready`, `/q/openapi`, Micrometer, tests, existing SHA identity `/api/info`, project naming conventions. Java 21 and Quarkus 3. Existing `quarkus-reference` is the baseline; only deviate with explicit justification. Prefer service repos to preserve the Golden Path's real workflow.

## Environment assumptions to verify

- Target namespace `<service>-dev` is the Golden Path default for newly scaffolded services. Inspect actual service naming and existing GitOps onboarding before changing namespace plans.
- Internal service traffic uses cluster DNS; external Routes only for the console/BFF and explicitly approved inference or diagnostic endpoints.
- Existing storage class, registry, cert issuer, GitOps operator and pipeline integration should be **discovered, not recreated**.
- No operator installation or cluster mutation from application prompts. For unavailable Kafka/VM/mesh/KServe, provide manifests and a clear readiness checklist, then stop that integration slice.
- Do not assume the prerelease OCP cluster supports an operator API until its CRD/operator compatibility is validated.

## Configuration

- Externalized config via environment variables and Secret references; supply `application.properties` examples with **dummy names**, not actual credentials.
- Request/limit, probes, pod security posture, network-policy needs, structured logs, scrape annotations/service monitors as relevant.
- Versioned Flyway SQL migrations for each authoritative database.
- Every generated repo includes `README.md`, `docs/architecture.md`, `docs/runbook.md`, `openapi.yaml` or generated equivalent, tests, `.github`/Golden Path pipelines inherited from template, and component metadata for Developer Hub.

## GitOps invariants

- Build container and publish image through existing pipeline only.
- No mutable `latest` tags for releases; deploy digest pinned via GitOps PR.
- No Tekton-run `oc apply` to deploy app directly.
- No manual `oc patch` as the desired-state mechanism.
- If PR automation or permissions fail, output branch/PR-ready patches and document blockers; never falsely claim a merge, rollout, or successful deployment.
- All promotion to dev and rollback must be traceable to commit and image digest.
