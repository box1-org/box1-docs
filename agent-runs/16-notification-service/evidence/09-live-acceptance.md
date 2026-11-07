# Phase 7 live acceptance (2026-11-06 13:30–13:40 EST)

Credential: the user issued the login `claude` to the run (2026-11-06). Tokens came from a scripted PKCE authorization-code login with no browser; the client has direct grants off. Tokens lived only in a mode-600 file in session scratch space. **The password and the tokens are not recorded anywhere in this repository.**

## Identity and roles (#59 check)

| Client | Token claims (non-secret) |
|---|---|
| `notification-service` | `typ=Bearer`, `azp=notification-service`, `aud=notification-service`, `resource_access.notification-service.roles=[notification-fault-operator, notification-reader]` |
| `operations-console` | `azp=operations-console`, roles `[console-viewer, console-developer, console-operator]` |

Both client roles exist on the cluster: the operator created them, and they appear in issued tokens.

## Access through the Route

| Request | Result |
|---|---|
| Reader token: `GET /api/v1/notifications?orderId=…` | 200 |
| Reader token: `GET /api/v1/stub` | 200; gate open in `notification-service-dev` |
| Console token: `GET /api/v1/notifications` | 200 (D-007 console acceptance) |
| Console token: `POST /api/v1/stub/faults`, `GET /api/v1/stub/faults/audit` | 403 `FORBIDDEN`; audited `DENIED_FORBIDDEN`, actor `claude` |
| Anonymous, garbage token (`07-live.md`) | 401 |

**Not proven live:** a token that lacks only `notification-reader` getting 403 on the read API. The issued user holds the reader role on both clients, so no such token was available. This is proven in CI (`SecurityTest`).

## Real order with the approved stub 503 run

The user approved one synthetic order with an unknown SKU and one `TRANSIENT_503` run.

- **Clocks:** host and Podman VM agreed (18:38:02 / 18:38:03 UTC).
- **Order request:** recorded before sending.
  - Idempotency-Key `run16-probe-4069ab5a-12cd-4a57-943b-1038e6243683`.
  - Synthetic `customerId` `cust_run16_probe_c7478a60`.
  - SKU `run16-NOSUCH-SKU`, quantity 1, `site_nyc`.

| Step | UTC | Result |
|---|---|---|
| Set fault `TRANSIENT_503`, `failCount` 2, TTL 120 s | 18:38:03 | 200; audit `SET … ACCEPTED claude` |
| `POST /api/v1/orders` | 18:38:03 | 201, `ord_b84bd53fc0514c86bf4598e29cda8ff6`, traceId `497a3c16d44b7161023c4c704a7033d6` |
| Inventory rejects; order-service publishes `order.state-changed.v1` → `REJECTED` / `UNKNOWN_SKU` | 18:38:08 | Notice `ntf_4a74af74892d0035a47131fa55` created: `ORDER_REJECTED`, `ops-orders`, `ORDER_REJECTED@v1` |
| Attempt 1 | 18:38:09 | TRANSIENT, `PROVIDER_UNAVAILABLE`, 503 |
| Attempt 2 | 18:38:12 | TRANSIENT, `PROVIDER_UNAVAILABLE`, 503 |
| Attempt 3 | 18:38:17 | SUCCESS, 202; receipt `rcpt_4b678ff053dc7f03c1bf2809` (body hash and length only) |
| Fault ends after its call budget | 18:38:17 | audit `EXHAUSTED … system` |
| Clear (`DELETE`) | 18:38:35 | 200; audit `CLEAR … NO_ACTIVE_FAULT claude` |
| Recheck 25 s later | — | still `count 1`, DELIVERED, 3 attempts |

Notice text: "Order ord_b84bd53fc0514c86bf4598e29cda8ff6 was rejected with reason UNKNOWN_SKU."

- **Trace link:** the notice's `traceparent` is `00-497a3c16d44b7161023c4c704a7033d6-…`, the same trace ID as the order. `correlationId` matches the order's.
- **Published event:** exactly one `notification.delivered.v1` on `box1.notification.events.v1`, keyed by the orderId, with the same receipt and `attemptCount` 3.
  - It validates against the box1-ops-contracts `main` envelope and payload schemas (ajv, from the `run16-contracts` worktree).
  - `aggregateId` equals `orderId`; `causationId` is the state-change `eventId`.
- **Customer identifier scan** for `cust_run16_probe_c7478a60`:

  | Where | Matches |
  |---|---|
  | API response | 0 |
  | Pod log (32 lines; 5 mention the order) | 0 (also 0 for `cust_`) |
  | Published event | 0 |

## Side effects

- One synthetic order exists in order-service: `ord_b84bd53f…`, REJECTED. Nothing was reserved or shipped.
- Reading the events topic ran `kafka-console-consumer.sh` via `oc exec` in the broker pod. That creates an ephemeral `console-consumer-*` group and produces nothing.
- Fault-control audit rows for the run, actor `claude`.

## Gap noticed

`GET /api/v1/stub/faults/audit` does not return the new `actor_subject` column. It is stored in the database but not exposed through the API. This is low severity and recorded as a follow-up.
