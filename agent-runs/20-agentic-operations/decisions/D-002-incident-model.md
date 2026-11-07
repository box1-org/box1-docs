# D-002 Incident identity and resolution

**Status:** proposed (agent). Aligned with operations-console `Incidents.java`.

- `{id}` in `POST /api/v1/ai/incidents/{id}/analyze` must match `inc_` + the contracts' order ID pattern. Anything else returns `400 INVALID_INCIDENT_ID`.
- The service resolves the order through order-service. If the order is unknown, the response is `404 INCIDENT_NOT_FOUND`, and no model call is made.
- The incident type is re-derived from order state with the same rules as the console: `ORDER_EXCEPTION`, `AWAITING_ERP_TOO_LONG`, or `NONE`. The threshold `AIOPS_STUCK_THRESHOLD` defaults to `10m`, the same as `console.stuck-threshold`. The service does not copy console code; the rule is small and both sides are tested.
- An order with no current incident can still be analyzed. The analysis then reports a "healthy control" result and must not invent a fault.
- The service keeps no incident store. Incidents stay derived, as in the console.
