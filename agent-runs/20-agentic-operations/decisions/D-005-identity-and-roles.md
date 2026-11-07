# D-005 Identity, roles and customer data

**Status:** proposed. GitOps changes need approval (Q-5). Operator-only v1 is to be confirmed (Q-4).

- **Keycloak client `agentic-operations`** (box1-gitops, scenario-controller pattern):
  - confidential, with a service account, `fullScopeAllowed: false` and the `roles` default scope;
  - client roles `aiops-viewer` (read evidence and analyses) and `aiops-analyst` (viewer, plus start analyses).
- **Public client `agentic-operations-cli`** for people and MCP clients: standard flow with PKCE, an audience mapper for `agentic-operations`, and a scope mapping for the two roles only. This follows `scenario-controller-cli`. Accepted `azp` values: `agentic-operations-cli`, plus `operations-console` later (#18).
- **Service account upstream roles:**
  - none for order, fulfillment and inventory, which are permit or unauthenticated in dev;
  - `asset-service` `telemetry-reader` for alerts. This needs the asset-service client scope mapping and `agentic-operations` added to `ASSET_READ_CLIENTS` in asset-service's workload, which is another service's config and so a stop (Q-5).
- **Customers:** box1 has no customer identity. v1 is **operator-only**: a token without an `aiops-*` role gets 403. To prevent leaks:
  - every evidence call is scoped to the requested order or asset;
  - no tool lists orders across customers;
  - analyses never include another order's data;
  - `customerId` appears only as the identifier already in the incident's own order.
- Customer-scoped access is a follow-up.
