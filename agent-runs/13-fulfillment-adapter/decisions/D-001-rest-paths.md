# D-001 REST path naming

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Gap:** the prompt and issue name `POST /api/fulfillments` and `GET /api/fulfillments/{fulfillmentRequestId}`; `01_DOMAIN_CONTRACTS.md` also lists the repository convention `/api/v1/...` and a protected `POST /internal/v1/fulfillments/{orderId}/reconcile`.

**Options:** A (chosen) use the prompt's names exactly, plus `POST /internal/fulfillments/{fulfillmentRequestId}/reconcile` for the operator action that moves a needs-attention request back to dispatch. B `/api/v1/fulfillments` with an alias. C both.

**Consequences:** One canonical path per operation; no alias to keep in step. The reconcile path is keyed by `fulfillmentRequestId`, not `orderId`, because one order may in future have more than one request. The adapter's OpenAPI documents the deviation from `/api/v1/`.
