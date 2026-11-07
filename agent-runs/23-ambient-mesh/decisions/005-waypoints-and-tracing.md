# 005 Waypoints and L7 tracing — proposed

- One waypoint per namespace: a `Gateway`, `gatewayClassName: istio-waypoint`, `istio.io/waypoint-for: service`, in `operations-console-dev`, `order-service-dev` and `inventory-service-dev`.
- Each namespace gets the label `istio.io/use-waypoint: waypoint`.
- Before merge, check with a server-side dry run that waypoint pods pass `restricted` Pod Security.
- Resource requests: 50m CPU and 128Mi each, with limits 500m and 256Mi.
- **Tracing:** add `meshConfig.extensionProviders` entry `box1-otel` (OpenTelemetry, `box1-collector.box1-observability.svc.cluster.local:4317`), and a `Telemetry` resource in each of the three namespaces only, with 100% sampling.
  - The waypoint spans join the application's W3C trace, so one `orderId` shows the L7 hop in Tempo.
- The collector's NetworkPolicy must admit waypoint pods.
- Rollback: remove the `use-waypoint` label, then the `Gateway`.
