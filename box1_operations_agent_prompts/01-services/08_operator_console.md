# Service 08 — Web application / operator console


> **Agent task:** Implement this service in `box1-org` using existing platform patterns. This prompt is deliberately smaller than a 64K model context: **under the `qwen-64k` profile, 64K is the maximum total context envelope, not a prompt length target.** Before changing code, inspect actual repo/template state. Follow `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. If shared docs are unavailable, the architectural invariants summarized below still apply. Backlog: [box1-docs#18](https://github.com/box1-org/box1-docs/issues/18).

**Mandatory operating constraints:** Quarkus 3 / Java 21 / Maven + existing Golden Path for Java services, REST/OpenAPI, health, Micrometer, correlated traces and structured logs, externalized config, tests, least privilege, PR+GitOps deployment, no direct Tekton deployment. Deliver one scoped acceptance slice under `qwen-64k`, or this service's vertical slice under `frontier`; never the entire backlog. Do not overwrite the validated `orders-service` example. Do not create or expose real credentials. Never assert success without running the validation.


**Priority / requirements:** P0 · FR-04; P1 · FR-08/09, NFR-09

**Dependencies:** the order, inventory, fulfillment adapter and asset telemetry APIs; the Keycloak `box1` realm; the shared box1 brand mark. The full BFF ([#17](https://github.com/box1-org/box1-docs/issues/17)) and the scenario controller ([#19](https://github.com/box1-org/box1-docs/issues/19)) are optional: the console works without them and uses them when they exist.

## Mission and boundary

Implement the visible **product**, not another cluster console. Proposed repo `box1-org/box1-ops-console`. Use TypeScript/React and an accessible component library, with the approved box1 identity: minimal charcoal/steel monochrome, geometric cube/“1” mark, restrained grid motif. Use the standalone logo asset from the box1 brand kit rather than regenerating random logo variations.

**Shape (user decision, 2026-11-05).** The console is one Golden Path Quarkus service with two parts in the same pod:

- **Front end:** a TypeScript/React single-page application, built during the Maven build from a pinned lockfile and served as static resources by Quarkus. Nothing loads from a CDN or external font service at runtime.
- **Console backend:** the Quarkus side holds the Keycloak login session and calls the services on the operator's behalf. Access and refresh tokens never reach browser JavaScript or browser storage. It exposes only the endpoints the console pages need, under its own versioned OpenAPI, and owns no business state.

The console backend is not the full BFF. [#17](https://github.com/box1-org/box1-docs/issues/17) keeps the cross-console aggregation contract (overview, incident evidence, customer projections). Shape the console backend so #17 can replace or absorb it later without changing the pages: one typed client generated from the console backend's OpenAPI, with the same Problem JSON and `sourceStatus` semantics #17 specifies.

## Interfaces, domain behavior and implementation constraints

- Pages: operator home (business indicators, exception queue); order list (filters, sort, pagination); order detail (state, customer-safe metadata, reservation/fulfillment status and timeline); incident/evidence view; sites/assets; optional developer delivery panel in P1.
- Happy path: an operator can place/submit seeded order, track from submitted to shipped/completed, and see a human-readable timeline. A stuck order visibly shows “Awaiting ERP acknowledgement” and outstanding attempts.
- **ERP progress is shown precisely.** `ORDER-STATE.md` displays order state `FULFILLMENT_REQUESTED` as "Awaiting ERP acknowledgement". When the fulfillment adapter's status is available, refine it from the adapter's `dispatch`, `erpAcknowledgement` and `outcome` fields: queued for the ERP, uploaded and awaiting acknowledgement, accepted by the ERP (`PENDING`), held by an ERP operator (`HELD`, which is not a failure), shipped, rejected, or needs attention. When the adapter cannot be reached, show the order service's state with "ERP detail unavailable", never a guessed adapter state.
- UX must connect each business state to trace ID / correlation ID / linked log/dashboard change evidence without forcing OpenShift admin access. Expose partial/unknown states honestly when backend observations are missing.
- Auth role-specific navigation and forbidden states; never rely on hiding buttons for real authorization. OIDC integration by config; no authentication bypass as the main deployed path. The console backend enforces every role check; the pages only reflect them.
- API client generated/validated from versioned OpenAPI (the console backend's now, the BFF's once it exists); typed error shapes and graceful loading/empty/error states. No direct browser calls to internal Kafka, PostgreSQL, VM admin interfaces, or other services' Routes.
- Calls from the console backend to each service use a token that service accepts, with least privilege and short timeouts. A dependency that is slow or refuses the call yields a partial page with a named failed source, not infinite loading.
- Branding: parent **box1**, product **Operations**. Do not overfocus on domain registration year. Responsive layout, meaningful keyboard focus, WCAG-conscious contrast, reduced motion, ARIA tables/alerts, automated accessibility checks.
- Demo control (P1): start/stop only authorized named fault scenarios through secured backend with warning, namespace/environment display and confirmation. No browser-embedded kubeconfig or generic remote command console. Named scenarios come from the scenario controller (#19) when it exists; telemetry load and chaos stay in the asset telemetry service's own console (`05_telemetry_service.md`), which this console may link to but does not duplicate.
- Synthetic demo user/customer/warehouse fixture list and screenshots in `docs/demo-walkthrough.md`.
- Browser testing uses Playwright or equivalent with Firefox or WebKit, never Chrome or its extension.

## Acceptance evidence (automate where practical)

- Playwright or equivalent E2E: seed order → submit → watch timeline; hold the request in the ERP console or delay ERP processing → see the waiting state with correct diagnosis links → recover → visibly complete.
- Browser role/customer checks and negative unauthorized API test.
- Keyboard-only order and incident traversal; a11y scan and mobile-width smoke test.
- Stable UI error/empty/loading states; no UI claim of resolution before the backend confirms it.
- Logo and favicon follow provided box1 brand assets and are license/project-owned.
- The console backend holds the session: no access or refresh token is readable by page JavaScript or stored in browser storage; anonymous console API calls get 401 and calls without the needed role get 403, through the real Route.
- Order detail distinguishes queued, awaiting ERP acknowledgement, accepted by ERP, held, shipped, rejected and needs attention from the adapter's status, and shows "ERP detail unavailable" when the adapter cannot be reached.
- The React/TypeScript front end is built by the existing Golden Path pipeline from a pinned lockfile and served from the console pod, with no CDN or external font at runtime.

## Recommended 64K-safe implementation slices

1. Scaffold branded shell, layout, typed API client and route/auth guards.
2. Order create/list/detail timeline and deterministic fixture flow.
3. Exceptions, telemetry and evidence links; partial-source messages.
4. Role/accessibility/E2E tests, demo screenshots and GitOps route.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** this console (front end and console backend), its OpenAPI, Keycloak client declaration, manifests and documentation. The full BFF (#17), the scenario controller (#19) and changes to any other service are out of scope; a needed change to another service is a stop condition. **Background:** the earlier pilots' `pilot-log.md` files, and the asset telemetry console in `box1-org/asset-service`, which already solved Keycloak browser login on this platform.

**Discovery must cover (state observed 2026-11-05 America/New_York; verify before relying on it):**

- the repository: no console repository existed. Onboarding one through the Golden Path is an approval-required action for the user; confirm its name (`box1-ops-console` was only proposed);
- the build: the Golden Path runs the `box1-quarkus-maven` cluster task in `box1-ci`. Whether it can run a Node build and fetch npm packages is not established; changing that shared task is outside scope;
- the release smoke task requires unauthenticated `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi` and `/q/metrics` (see [#40](https://github.com/box1-org/box1-docs/issues/40));
- the APIs, from `box1-ops-contracts/openapi/` and each service's served OpenAPI:
  - order service: `/api/v1/orders` (create, list), `/api/v1/orders/{orderId}` and `/timeline`. It has **no authentication** ([#40](https://github.com/box1-org/box1-docs/issues/40)), and its CORS allows only Developer Hub;
  - inventory service: `/api/v1/inventory` and `/api/v1/reservations/{reservationId}`, bearer tokens;
  - fulfillment adapter: `GET /api/fulfillments/{fulfillmentRequestId}` for any authenticated caller, writes need `fulfillment-writer`; status fields `dispatch`, `erpAcknowledgement`, `outcome`;
  - asset service: readings and `/api/v1/alerts` need `telemetry-reader`, and it requires `azp=asset-service`, so a token issued to another client is refused;
  - how an order maps to its `fulfillmentRequestId`, and whether that link is available through an API;
- Keycloak: realm `box1` in `box1-gitops/platform/identity/keycloak/realm/`, RH-SSO 7.6 operator, clients `developer-hub`, `openshell-cli`, `asset-service` and `fulfillment-adapter`. Client roles declared in `spec.roles` were not created by the operator ([#59](https://github.com/box1-org/box1-docs/issues/59)); the documented mitigation is a manual step;
- the asset-service console's login lessons: a public client with PKCE, a separate `web-app` OIDC tenant chosen by path, and a session key generated per process that signs users out at every restart ([#63](https://github.com/box1-org/box1-docs/issues/63));
- the brand mark: the asset-service console uses the `box1-org` organization avatar, supplied by the project owner, unmodified (SHA-256 recorded in its `docs/architecture.md`). Confirm with the user that it is the brand-kit asset and that a favicon may be derived from it by resizing only;
- whether the ERP harness, the ERP VM (#25) or the deployed adapter can show a held request, which the E2E acceptance needs.

**Design decisions to record before implementation:**

- the front-end build inside Maven (for example Quinoa or the frontend Maven plugin), the pinned Node version, lockfile and registry access, and how the result is served with a correct SPA fallback and cache headers;
- the Keycloak client and roles for the console (for example operator, developer and admin), confidential or public, and how the console backend obtains tokens each service accepts: token exchange, a service-account client, or audience mappers. A GitOps PR that needs approval; a change to another service's accepted audiences or `azp` is a stop condition;
- the session: cookie settings, CSRF protection for state-changing calls, logout, and the session encryption key. A stable key is a new secret and needs approval; without it, keep one replica and record the limit, as #63 did;
- the order service while #40 is open: whether the console backend calls it unauthenticated in-cluster, and how the Route exposure is recorded. The console must not make #40 worse;
- whether the customer role is in scope for this run, given that orders carry no verified customer identity yet;
- the console backend's endpoint list and OpenAPI, mapped to #17's endpoints so absorption later is a straight swap;
- timeouts, concurrency bounds and caching for each upstream, and the `sourceStatus` shape;
- how ERP progress maps from adapter fields to the labels above, and how an order finds its fulfillment status;
- trace propagation from browser to console backend to services, and which evidence links (trace, log, dashboard, Git SHA) exist today versus later with #22;
- the demo control: deferred until #19 exists, or a link to the telemetry console;
- the deterministic seed fixtures and how they are reset without touching other data.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Pipeline Node capability established; token acceptance of each upstream recorded |
| 2 Contracts | The console backend's OpenAPI reviewed; no change to another service's contract |
| 3 Implementation | Every role check is in the backend; the pages contain no authorization the backend does not repeat |
| 4 Verification | All scenarios below run; each result is in the ledger |
| 5 Review | The full suite is rerun after reviewer repairs; the Security pass covers session, CSRF, token handling and the Route |
| 6 Delivery | The front end builds in the Golden Path pipeline; release gates pass or the blocker is recorded; promotion is for this service only |
| 7 Live acceptance | Sign in through the real Route; one order followed from submit to shipped with its ERP progress and evidence links, after approval |

**Verification scenarios:** anonymous request to every console API path; signed-in user without the needed role; tokens absent from page JavaScript and browser storage; CSRF on a state-changing call; logout ends the session; each upstream slow or down in turn gives a partial page with the failed source named; adapter unreachable shows "ERP detail unavailable"; a held ERP request shows as held, not failed; order submitted twice with the same idempotency key creates one order; keyboard-only order and incident traversal; automated accessibility scan; mobile-width smoke; pod restart behavior of the session, observed and recorded; the browser makes no request to a host other than the console's own Route and Keycloak.

## Agent finish-line checklist

- Add/update OpenAPI, relevant event schema fixtures, tests, migrations, config documentation and runbook.
- Run targeted unit/integration/contract tests and report real command output. Do not confuse generated files with a deployed system.
- Record trace/log/metric correlation, health endpoints, request/limit proposals and security boundaries.
- Prefer the existing Golden Path + GitOps promotion; provide PR-ready changes and an exact next handoff if permissions/operators aren't available.
- Summarize touched files, requirements satisfied, assumptions, remaining blockers and next smallest slice in `00-shared/05_HANDOFF_TEMPLATE.md` format. Under `frontier`, also complete its run state block.
