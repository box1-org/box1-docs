# D-004 MCP surface

**Status:** the MCP surface was decided by the user (evidence and analysis tools); the details are proposed. The extension version waits on a build check (Q-2).

- **Extension:** `io.quarkiverse.mcp:quarkus-mcp-server-http` with `quarkus-mcp-server-oidc`.
  - Use stable **2.0.4** if it builds and its tests pass on Quarkus 3.40.1.1.
  - Otherwise stop. Using **2.1.0.Beta1** (built on Quarkus 3.40.1) is a pre-release and needs the user's approval.
  - Use the BOM if one is published.
- **Transport:** Streamable HTTP at `/mcp`. The legacy SSE endpoint is disabled if configurable.
- **Exposed:** tools only. No resources, prompts or sampling.
- **Tools.** Each tool calls the same `EvidenceService` or `AnalysisService` methods as REST.

| Tool | Args | Role |
|---|---|---|
| `get_order_timeline` | `orderId` | `aiops-viewer` |
| `get_fulfillment_status` | `orderId` (resolved to fulfillmentRequestId through the window) | `aiops-viewer` |
| `get_inventory_reservation` | `orderId` | `aiops-viewer` |
| `list_recent_events` | `orderId` or `assetId`, `limit` ≤ 50 | `aiops-viewer` |
| `list_telemetry_alerts` | `assetId`, optional | `aiops-viewer` (`UNAVAILABLE` until Q-5) |
| `get_deployed_revision` | `service` from an allowlist | `aiops-viewer` |
| `analyze_incident` | `incidentId` | `aiops-analyst` |
| `get_analysis` | `analysisId` | `aiops-viewer` |

- **Authorization:**
  - `quarkus.http.auth.permission` requires an authenticated bearer token on `/mcp/*`.
  - Each service method checks roles with `@RolesAllowed`, so REST and MCP get the same decision.
  - A `ToolFilter` may hide tools a caller cannot use, but filters fail open (evidence/01), so they are never the enforcement point.
- **Arguments:** validated against the contracts' ID patterns. An unknown tool or invalid arguments return a protocol error, and no upstream call is made.
- **Results:** structured content `{untrusted: true, source, retrievedAt, retrievalStatus, data}`. Text fields are bounded in length.
- **Audit:** an INFO log line per call with tool, subject, roles, decision, duration, result bytes and traceId. It never contains argument values beyond IDs, nor any evidence content.
