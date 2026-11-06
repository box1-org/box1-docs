# D-008: Controller design

- **Status:** decided by the agent, 2026-11-06.

## API (`/internal/v1`)
- `GET /scenarios`: the catalog, each entry with `name`, `title`, `description`, `mechanism`, `availability`, `notPossibleReason`, `fixtures`, `maxDurationSeconds`, `expectedObservation`, `resetAction`, `operatorSteps`. `name` and `description` keep #18's current read shape working.
- `POST /scenarios/{name}/start` (body optional: `{ttlSeconds}`), `POST /scenarios/{name}/stop`, `POST /scenarios/{name}/reset`. Stop and reset apply to the active run of that scenario; reset with no active run restores the fixture state and records it.
- `POST /fixtures/seed`: seed or verify the fixture set (idempotent).
- `GET /runs`, `GET /runs/{scenarioRunId}`, `GET /audit`.
- Errors are RFC 9457 Problem JSON with plain text, e.g. "Scenario `erp-unavailable` is not allowed in namespace `x`".

## Execution model
- **No generic execution.** Each available scenario is a Java class with fixed steps. Outbound HTTP goes only to base URLs fixed in configuration per service; no request field becomes a URL, command or path segment other than validated fixture IDs.
- **Not yet possible** scenarios are catalog entries with a reason and no code. Starting one returns 409 and is audited as `DENIED`.
- **One active run at a time** across the controller (fixture state is shared). A second start returns 409.
- Run states: `RUNNING` → `AWAITING_OPERATOR` (guided) → `VERIFIED` | `NOT_VERIFIED` | `FAILED` | `STOPPED` | `EXPIRED` | `ABORTED_RESTART`, then the reset result `RESET_OK` | `RESET_FAILED` | `RESET_GUIDED` (an operator step whose effect the controller cannot observe).
- Every run gets `scenarioRunId` `scn_<20 hex>` and correlation marker `scenario-<scenarioRunId>`, sent as `X-Correlation-Id` with W3C `traceparent` on every call. Order idempotency keys are `stardock-<scenarioRunId>-<n>`; `X-Consumer-Id: scenario-controller`.
- **Verification** reads business state: order state and timeline, inventory reservation counts and stock, adapter status (matched by `orderId`). Success is reported only after the invariant holds.

## Guided ERP steps
- The run shows the exact console keystrokes and the order or fulfillment ID, enters `AWAITING_OPERATOR`, and polls the adapter's status until the expected observation (for example `outcome=HELD`, then not `HELD`) or the run's TTL. A timeout is `NOT_VERIFIED`, never success.
- The fulfillment ID comes from order-service's internal `ful_<order suffix>` naming (no published link, #18 G-1). The adapter's `orderId` must match, so a naming change fails closed.

## TTL and crash recovery
- Each scenario has a default and maximum duration in the catalog; `ttlSeconds` may only lower it. `expiresAt` is stored at start.
- A scheduler every 5 s expires overdue runs and runs their reset. The controller has one replica; at startup every run not in a terminal state becomes `ABORTED_RESTART` and is reset. Nothing resumes silently.
- Manual recovery (runbook): `POST /scenarios/{name}/reset` resets fixture stock; guided steps list the console step to undo.

## Audit
- PostgreSQL tables `scenario_run` and `scenario_audit` (append-only, immutable triggers), recording actor (token subject), time, environment, namespace, mode, TTL, impact (fixture IDs and order IDs), outcome and reset result. Refusals are audited as `DENIED`.
- Retention 90 days. A daily job deletes older rows through a SQL function that is the only permitted delete path.
- **Stardate (display only):** `1000 × (year − 2323) + 1000 × fraction of the UTC year elapsed`, one decimal (2026-11-06 00:00 UTC ≈ −296151.2). Shown beside the ISO 8601 timestamp; the timestamp is authoritative.

## Observability
- JSON logs with `scenarioRunId` and correlation ID in MDC; OpenTelemetry spans for each step; Micrometer counters `scenario_runs_total{scenario,outcome}`, gauge `scenario_active_runs`.
