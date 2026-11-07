# Phase 7: live acceptance (non-fault part)

Run 2026-11-07 ~00:45 EST against `https://agentic-operations-dev.apps.ocp.box1.org`, with the service at `9d2d3e3` (digest `sha256:21da40d4…`).

## Identity

- **Login:** the user assigned the `aiops-*` roles. A token was obtained with the **device authorization grant plus PKCE** on `agentic-operations-cli`. The user approved it in their own browser, and the agent never handled the password. The approving account was **`mike`**, not the `claude` login the user mentioned.
- **Token claims:** `aud=agentic-operations`, `azp=agentic-operations-cli`, and `resource_access` contains only `agentic-operations` with roles `aiops-analyst` and `aiops-viewer`. **This proves the preset-ID scope mapping from box1-gitops#99 works.** The token lifetime is 300s.
- **Storage:** the token was kept in a mode-600 file in the session scratchpad, was never printed, and is not in this repository.

## REST

The test order was real order `ord_2f6bb653158242adbc3bfa81b6ccb4d7` (SHIPPED; no stuck or exception order existed at the time).

| Check | Result |
|---|---|
| `POST /api/v1/ai/incidents/inc_<order>/analyze` | 202, `ana_8c3bb247…` |
| Analysis | **COMPLETED** in 4.2s; `incidentType=NONE`; model `box1-coder`, profile 32k, 4718 prompt and 222 completion tokens |
| Evidence | ev_1 ORDER, ev_2 ORDER_TIMELINE, ev_3 KAFKA_EVENTS, ev_4 **FULFILLMENT** (found through the Kafka window, which covers #78), ev_5 RESERVATION, ev_6–8 DEPLOYED_REVISION, ev_9 TRACE_REFERENCE: all **OK**. ev_10–13 TELEMETRY_ALERTS, TRACE_CONTENT, METRICS_AND_ALERTS and LOGS are **UNAVAILABLE** and are listed in unknowns |
| Model answer | Summary says the order "progressed normally … shipment was confirmed. No faults or errors are indicated". 0 findings, 0 unsupported, the only action `NO_ACTION` (`executable=false`). No fault invented on the healthy control |
| Unknown incident `inc_ord_doesnotexist00` | 404 |

## MCP (Streamable HTTP, same token)

| Check | Result |
|---|---|
| `initialize` | 200, with a session |
| `tools/list` | exactly the 8 catalog tools |
| `get_order_timeline` | `untrusted: true`, OK, 4 entries |
| `list_recent_events` | 8 events for the order from the live window |
| `get_order_timeline` with `orderId="https://evil.example/x"` | `isError: true`, no upstream call, audit `id=invalid decision=invalid_argument` |
| `analyze_incident` then `get_analysis` | COMPLETED in 4.1s. **Evidence types and statuses are identical to the REST analysis** |

## Tracing (Tempo, tenant `dev`, read with the operator's own `oc` token)

- **REST path:** one trace contains `agentic-operations: POST /api/v1/ai/incidents/{incidentId}/analyze`, then `aiops.analysis`, then order-service (order, timeline, info), inventory-service (reservation, info) and fulfillment-adapter (fulfillment, info). **The trace spans four services**, so context propagation into the worker and W3C `traceparent` on the outbound calls work.
- **MCP path:** the `aiops.analysis` trace has all the downstream spans but **no parent span for the MCP HTTP request**. The MCP endpoint creates no server span, and its log lines have no traceId. This is a low-severity gap and becomes a follow-up.
- vLLM exports no spans, as expected.

## Logs

- Audit lines carry only tool, ID (or `invalid`), subject, decision, duration and size.
- Model lines carry only outcome, tokens and profile.
- Worker lines carry `traceId` and `analysisId` in MDC.
- `grep` for token fragments and evidence text found 0 matches.

## Not done in this part

- **The seeded ERP slowdown (`erp-delayed-processing`):** it injects a fault and is waiting for the user's approval.
- **A viewer-only 403 on analyze, and a token without a role:** the account holds both roles. CI covers these.
- **A restart check:** it needs a pod restart, which is a cluster mutation that needs approval. The analysis-404 after a restart is proven in CI; the window refill was observed live at startup (`evidence/09`).
- **The Prometheus scrape:** not verified.
