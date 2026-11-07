# D-013 Contracts

**Status:** proposed. Needs a box1-ops-contracts PR, merged with approval.

- Shared change: the `TOPICS.md` consumer-group column only, as in D-007.
- Not shared:
  - the REST OpenAPI and the MCP tool catalog are owned by the service, in its repo under `docs/` and `src/main/resources/META-INF/openapi.yaml`;
  - event schemas are consumed from `events/v1` at a pinned contracts commit and never copied, as the notification-service build does (to be confirmed at phase 3).
