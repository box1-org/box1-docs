# D-012 Observability and resources

**Status:** proposed.

- **Tracing:** OTel environment as in operations-console (`QUARKUS_OTEL_EXPORTER_OTLP_ENDPOINT=http://box1-collector.box1-observability.svc:4317`, sampler 1.0). The `traceparent` from Kafka events is recorded as a reference only; consumption does not continue those traces.
- **Logs:** structured JSON with `traceId`, `analysisId`, `incidentId` and tool name. No prompt, completion or evidence content is logged.
- **Metrics:**
  - `aiops_analyses_total{status}`;
  - `aiops_analysis_duration_seconds`;
  - `aiops_model_tokens{kind}`;
  - `aiops_queue_depth`;
  - `aiops_mcp_tool_calls_total{tool,decision}`;
  - `aiops_evidence_fetch_total{source,status}`;
  - the window metrics (D-007).
- **Monitoring resources:** a ServiceMonitor, plus a PrometheusRule for the model being unavailable for 10m and for a window that has not refilled.
- **Resources:** requests 100m CPU and 384Mi memory, limits 1 CPU and 768Mi. One replica (D-003).
- **Probes:** readiness does not depend on Kafka or the model.
