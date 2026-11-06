# box1 Operations console — functional capabilities (draft for discussion)

Source: [box1-docs#18](https://github.com/box1-org/box1-docs/issues/18) and prompt `box1_operations_agent_prompts/01-services/08_operator_console.md`.
Status: **discussion draft**. Nothing here is implemented or deployed. The mockup in this folder is a static HTML file with synthetic data.

Priority follows the issue: **P0** = FR-04; **P1** = FR-08/09, NFR-09. These FR/NFR IDs are **not defined** in any local document. The mappings marked "?" are inferred from tags, not from a definition.

| # | Area | Capability | Pri | Expected data source | Mockup screen |
|---|---|---|---|---|---|
| C1 | Shell | Branded shell (box1 / Operations), responsive nav, skip link, environment/namespace badge, data-freshness indicator | P0 | static + `GET /api/v1/overview` | Header on every page |
| C2 | Auth | OIDC sign-in; role-aware navigation (customer / operator / developer / admin); explicit forbidden state; authorization enforced by the BFF, not by hidden buttons | P0 nav · P1 roles (FR-08?) | OIDC + BFF 401/403 Problem | Ribbon role switcher; open `#/demo` as Developer; open `#/orders/ord_1043` as Customer |
| C3 | Home | Business indicators: submitted, awaiting ERP ack, stuck, exceptions, shipped/completed, active equipment alerts; sources that did not answer are labelled, not shown as zero | P0 | `/overview` | Home |
| C4 | Home | Exception queue: stuck and EXCEPTION orders with reason, outstanding ERP attempts, age, linked incident | P0 | `/overview` + order summary | Home → Exception queue |
| C5 | Orders | Order list: filter (state, site, text, needs-attention), sort, paginate, human-readable state chips | P0 (FR-04) | `GET /api/v1/orders` | Orders |
| C6 | Orders | Place/submit a seeded order with validation and idempotency | P0 | `POST /api/v1/orders` | Place order (try quantity 0, or `site_closed`) |
| C7 | Orders | Order detail: progress rail, customer-safe metadata, reservation, fulfilment attempts, notification outcome | P0 (FR-04) | `GET /api/v1/orders/{id}/summary` | Order `ord_1042` |
| C8 | Orders | Human-readable timeline (transitions + notes), each linked to event type, trace ID and correlation-ID logs. Customers see the timeline without internal links | P0 (FR-04) | `/orders/{id}/timeline` | Order detail → Timeline |
| C9 | Orders | Stuck-state banner: "Awaiting ERP acknowledgement — N attempts outstanding" with link to incident | P0 | order summary | Order `ord_1043` |
| C10 | Evidence | Incident view: SLO breach, linked orders, evidence per source (traces, logs, metrics, changes) with `sourceStatus`; partial or unknown sources stated explicitly | P0/P1 | `GET /api/v1/incidents/{id}/evidence` (**schema assumed**) | Incidents → `inc_0007` |
| C11 | Evidence | No UI claim of resolution before backend confirmation: recovery moves Requested → Awaiting confirmation → Recovered only on backend signal | P0 | evidence / order summary | `inc_0007` → Request controlled recovery |
| C12 | Sites/assets | Sites (ACTIVE/UNAVAILABLE) with stock by SKU; assets with last reading, unknown readings, WARNING/CRITICAL alerts | P1 | inventory + asset APIs via BFF | Sites & assets |
| C13 | Demo control | Start/stop named fault scenarios only, with warning, environment/namespace display, explicit confirmation, TTL and audit trail; no kubeconfig or command console | P1 (FR-09?) | scenario controller via BFF | Demo control (Operator/Admin) |
| C14 | Dev panel | Deployed revision, image digest, Argo CD sync and health per service | P1 (optional) | BFF (**endpoint not defined**) | Delivery (Developer/Admin) |
| C15 | Cross-cutting | Loading / empty / error states with typed RFC 9457 Problem; keyboard traversal and focus on navigation; ARIA tables, alerts and live region; reduced motion; mobile width; state never shown by colour alone | P0 (NFR-09?) | — | Ribbon "Simulate data state"; resize to 390 px |

## Role → page matrix (proposed; FR-08 undefined)

| Page | Customer | Operator | Developer | Admin |
|---|---|---|---|---|
| Home | — | ✓ | ✓ | ✓ |
| Orders / detail | own only, no internal IDs | ✓ | ✓ (read) | ✓ |
| Place order | ✓ (self) | ✓ | — | ✓ |
| Incidents / evidence | — | ✓ | ✓ | ✓ |
| Request recovery | — | ✓ | button visible, server returns 403 | ✓ |
| Sites & assets | — | ✓ | ✓ | ✓ |
| Demo control | — | ✓ | — | ✓ |
| Delivery | — | — | ✓ | ✓ |

Operator access to Demo control follows prompt 09 ("behind admin/operator authorization").

## Happy-path and fault walkthrough (as clickable in the mockup)

1. As **Operator**, open **Place order**, submit SKU-42 × 2 at `site_nyc`, and land on the new order.
2. Press **Simulate next backend event** to step SUBMITTED → Stock reserved → Awaiting ERP acknowledgement → Shipped → Completed. The timeline grows with each step.
3. On **Home**, the exception queue shows `ord_1043` and `ord_1048` stuck under the running `erp-slowdown` scenario.
4. Open **inc_0007**. The evidence table shows Metrics as PARTIAL and Recent changes as UNAVAILABLE, with a banner explaining the gap.
5. Click **Request controlled recovery**, confirm, and the status reads "awaiting backend confirmation". Then click **Simulate backend confirmation**: the incident resolves, the linked orders complete, and the audit trail records the stop.

## Gaps and decisions needed

- **FR/NFR definitions:** FR-04, FR-08, FR-09 and NFR-09 are referenced but not defined anywhere.
- **Incident schema:** there is no contract. The mockup invents `incidentId`, `slo`, `evidence[].sourceStatus` and `recovery`.
- **BFF OpenAPI:** `07_experience_bff.md` describes `/overview`, `/orders/{id}/summary` and `/incidents/{id}/evidence` only in prose. Prompt 08 requires a generated client from a versioned BFF OpenAPI.
- **Observability link targets:** the trace, log and dashboard deep-link format, and the tool behind it, are undecided.
- **Delivery panel:** data source undefined; optional P1.
- **Exception reconciliation:** EXCEPTION means "manual reconciliation", but there is no workflow or endpoint.
- **Brand:** the only asset is `box1-mark.png`, 400×400 PNG copied from `run15-asset-service` (decision D-016). There is no SVG or brand kit.
