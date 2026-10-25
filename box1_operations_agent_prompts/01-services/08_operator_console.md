# Service 08 — Web application / operator console


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, and `03_QUALITY_GATES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply.

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice, not the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-04; P1 · FR-08/09, NFR-09

**Dependencies:** BFF REST API (or direct order read endpoints until BFF P1); optional OIDC provider and shared brand asset.

## Mission and boundary

Implement the visible **product**, not another cluster console. Proposed repo `box1-org/box1-ops-console`. Use TypeScript/React and an accessible component library, with the approved box1 identity: minimal charcoal/steel monochrome, geometric cube/“1” mark, restrained grid motif. Use the standalone logo asset from the box1 brand kit rather than regenerating random logo variations.

## Interfaces, domain behavior and implementation constraints

- Pages: operator home (business indicators, exception queue); order list (filters, sort, pagination); order detail (state, customer-safe metadata, reservation/fulfillment status and timeline); incident/evidence view; sites/assets; optional developer delivery panel in P1.
- Happy path: an operator can place/submit seeded order, track from submitted to shipped/completed, and see a human-readable timeline. A stuck order visibly shows “Awaiting ERP acknowledgement” and outstanding attempts.
- UX must connect each business state to trace ID / correlation ID / linked log/dashboard change evidence without forcing OpenShift admin access. Expose partial/unknown states honestly when backend observations are missing.
- Auth role-specific navigation and forbidden states; never rely on hiding buttons for real authorization. OIDC integration by config; no authentication bypass as the main deployed path.
- API client generated/validated from versioned BFF OpenAPI; typed error shapes and graceful loading/empty/error states. No direct browser calls to internal Kafka, PostgreSQL, or VM admin interfaces.
- Branding: parent **box1**, product **Operations**. Do not overfocus on domain registration year. Responsive layout, meaningful keyboard focus, WCAG-conscious contrast, reduced motion, ARIA tables/alerts, automated accessibility checks.
- Demo control (P1): start/stop only authorized named fault scenarios through secured backend with warning, namespace/environment display and confirmation. No browser-embedded kubeconfig or generic remote command console.
- Synthetic demo user/customer/warehouse fixture list and screenshots in `docs/demo-walkthrough.md`.

## Acceptance evidence (automate where practical)

- Playwright or equivalent E2E: seed order → submit → watch timeline; inject ERP slowdown → see exception with correct diagnosis links → recover → visibly complete.
- Browser role/customer checks and negative unauthorized API test.
- Keyboard-only order and incident traversal; a11y scan and mobile-width smoke test.
- Stable UI error/empty/loading states; no UI claim of resolution before the backend confirms it.
- Logo and favicon follow provided box1 brand assets and are license/project-owned.

## Recommended 64K-safe implementation slices

1. Scaffold branded shell, layout, typed API client and route/auth guards.
2. Order create/list/detail timeline and deterministic fixture flow.
3. Exceptions, telemetry and evidence links; partial-source messages.
4. Role/accessibility/E2E tests, demo screenshots and GitOps route.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format.
