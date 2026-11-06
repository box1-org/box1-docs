# 003 Collector shape and service export

- **Collector:** one `OpenTelemetryCollector` `box1` Deployment receiving OTLP gRPC (4317) and HTTP (4318). Processors: `memory_limiter` (75%) and `batch`. Exporter to `tempo-box1:4317` with a 2000-batch queue and 120 s of retries; spans are then dropped, never blocking services.
- **Services:** each service sets `QUARKUS_OTEL_TRACES_EXPORTER=cdi`, `QUARKUS_OTEL_EXPORTER_OTLP_ENDPOINT` and `deployment.environment=dev` through its kustomize ConfigMap. No image rebuild is needed. Metrics and log OTLP export stay `none`: metrics come from Prometheus scrape of `/q/metrics` and logs from stdout JSON.
- **Sampling:** the Quarkus default `parentbased_always_on` (100%) at lab load. Revisit after measuring the span rate.
- **Outage behaviour:** a collector or Tempo outage drops spans; business requests continue. To be proven in Phase 4.
