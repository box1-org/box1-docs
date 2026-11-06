# D-004 Calling the order service while #40 is open

**Status:** decided. It does not make #40 worse.

- The console backend calls `http://order-service.order-service-dev.svc:8080` **in-cluster without a token**, because the service accepts none.
  - There is no new Route and no CORS change, and the console's Route never proxies arbitrary order-service paths.
- **The console enforces its own roles:** reads need `console-viewer` or higher, and create needs `console-operator`. Anyone can still bypass the console through order-service's own Route. That is #40's exposure, unchanged. The UI and docs state it.
- `X-Consumer-Id: operations-console` is sent on create, so console-originated idempotency keys share one scope.
  - Per #40, this is not an identity, and another caller can collide with the scope.
  - The console generates a UUIDv4 `Idempotency-Key` per form submission and keeps it across retries of that submission. Duplicate submission returns the same order: 200 with `Idempotency-Replayed: true`.
- Once #40 adds token auth, the console's client gains an `order-service` audience in a later change.
