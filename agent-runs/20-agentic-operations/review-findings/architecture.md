# Architecture pass (phase 5)

Reviewer: a fresh subagent given the diff `61bcb8c..bed8e44`, the prompt, the contracts and the console's `Incidents.java`. It made no changes and did not run tests. Date: 2026-11-06 EST.

**Confirmed sound:**
- REST and MCP share one service layer, and `Guard` is the only place authorization happens.
- There is no path for writes, shell, Kubernetes or arbitrary URLs.
- The model gets no tools, and its output is validated.
- The service reads no other service's tables and joins no distributed transaction.
- Workers never touch the request-scoped identity.
- Producers set `aggregateId` to `orderId`, so keying the window on `aggregateId` is correct.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| A-1 | medium | The free-text `summary` is returned uncited, even when every finding was dropped as unsupported | **Repaired in `0cf2604`.** Repair: when the model's findings were all unsupported, replace the summary with fixed text and set `statusDetail`. A healthy result with no findings is unaffected |
| A-2 | medium | The store is written before the queue slot is reserved, so a BUSY response first evicts a real analysis | **Repaired in `0cf2604`.** Repair: submit to the executor first; the worker creates or updates the store entry. BUSY now touches nothing |
| A-3 | medium | The consumer group is not declared in the contracts | Same as M-1: the contracts PR (Q-7) |
| A-4 | medium | The console's `current()` keeps an order awaiting the ERP active below the threshold, but this service sends `NONE` | **Repaired in `0cf2604`.** Repair: mirror `current()`. `FULFILLMENT_REQUESTED` is `AWAITING_ERP_TOO_LONG`, with the elapsed time passed to the model. D-002 amended |
| A-5 | low | There is no correlation index | Same as M-3 |
| A-6 | low | Worker threads lose the OTel context and MDC, so analysis work isn't on the request trace | **Repaired in `0cf2604`.** Repair: wrap the task with the current OTel `Context`, and put `analysisId` in MDC |
| A-7 | low | The TTL counts from creation, while D-003 says after completion | **Repaired in `0cf2604`.** Repair: `expiresAt` is set when the analysis reaches a terminal status |
