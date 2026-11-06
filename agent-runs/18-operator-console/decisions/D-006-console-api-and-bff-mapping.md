# D-006 Console backend API, OpenAPI and #17 mapping

**Status:** decided.

- **Contract-first.** `src/main/resources/META-INF/openapi.yaml` (`info.version 1.0.0`) is the versioned contract. Quarkus serves it merged with the scanned annotations at `/q/openapi`.
  - The front end generates its types from **the same file** at build time (`openapi-typescript` to `src/api/schema.d.ts`) and calls the API through `openapi-fetch`, so there is one typed client.
  - A Java test checks every operation in the YAML against the served `/q/openapi`, so the implementation and the contract cannot drift.
- **Paths are #17's paths where #17 defines them**, so #17 can replace the backend by serving the same contract:

| Console path | Purpose | #17 equivalent |
|---|---|---|
| `GET /api/v1/me` | username, roles, environment | (console-specific; #17 needs the same) |
| `GET /api/v1/overview` | indicators and exception queue | `GET /api/v1/overview` |
| `GET /api/v1/orders` | windowed list with filter/sort/page (D-013) | (#17 list) |
| `POST /api/v1/orders` | place order (operator) | pass-through to order-service |
| `GET /api/v1/orders/{orderId}/summary` | order, reservation, fulfillment, ERP progress, timeline, evidence | `GET /api/v1/orders/{id}/summary` |
| `GET /api/v1/incidents` | derived incident list (D-012) | (#17) |
| `GET /api/v1/incidents/{incidentId}/evidence` | evidence with `sources` | `GET /api/v1/incidents/{id}/evidence` |
| `GET /api/v1/sites` | stock by site (inventory) and telemetry status | (#17) |
| `GET /api/v1/delivery` | each service's `/api/info` revision (developer) | (#17) |

- **Errors** are RFC 9457 `application/problem+json` with `type, title, status, detail, code`.
- **`sources`** (#17 calls it `sourceStatus`): every aggregate response carries a `sources` array of `SourceStatus` items:
  - `{source: order-service|inventory-service|fulfillment-adapter|asset-service|scenario-controller, status: OK|DEGRADED|UNAVAILABLE|NOT_AUTHORIZED|NOT_CONFIGURED, detail, latencyMs, observedAt}`
  - Values from a failed source are **absent** (null), never invented.
  - #17's prompt names the concept but defines no schema. This shape is offered to #17 as the schema.
- **Template paths** `/api/greetings` and `/api/info` stay public for the release smoke task (#40 list), along with `/q/health/*`, `/q/openapi` and `/q/metrics`.
