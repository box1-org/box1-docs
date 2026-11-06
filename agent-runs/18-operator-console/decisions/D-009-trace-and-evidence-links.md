# D-009 Trace propagation and evidence links

**Status:** decided.

- **Browser to console backend:** the typed client sends a fresh W3C `traceparent` per request.
  - `quarkus-opentelemetry` continues the trace and propagates `traceparent` to every REST client call.
  - Export stays `none`, like asset-service, until a collector exists (#22).
  - Logs are JSON (`quarkus-logging-json`) and carry `traceId`/`spanId` through MDC. They never include tokens, cookies or the request body.
- **Evidence shown per business state, without OpenShift access:**
  - **Available today:** each timeline entry's `traceId`, `correlationId`, `eventId`, `eventType` and `causationId` (copyable); the adapter `revision`, `statusAt` and counters; each service's deployed Git SHA from `/api/info`, linked to the GitHub commit.
  - **Later with #22:** trace, log and dashboard deep links, shown as "Not available until #22" rather than as dead links.
