# Q-2 MCP extension compatibility check

Run 2026-11-06 22:33 EST on agentic-operations branch `issue-20-agentic-operations` at `f6a072b`. Command: `./mvnw -B -ntp verify` (local, JDK 21.0.13).

- `quarkus-mcp-server-http` and `quarkus-mcp-server-oidc` **2.0.4** on Quarkus **3.40.1.1**: compile, augmentation and tests pass with no warnings.
- `McpCompatTest` checks `initialize` (returns an `Mcp-Session-Id`), `notifications/initialized` (202), `tools/list` (lists the probe) and `tools/call` (returns the expected text) over Streamable HTTP at `/mcp`.
- The first run failed only because Kafka Dev Services could not find Docker. It passed after setting `quarkus.kafka.devservices.enabled=false`, as the other services do.
- **Result:** Q-2 is resolved. Use stable 2.0.4; the beta is not needed.

```text
2026-11-06 22:33:08,359 INFO  [io.quarkus] (main) Installed features: [cdi, compose, kafka-client, mcp-server-http, mcp-server-oidc, messaging, messaging-kafka, micrometer, oidc, rest, rest-jackson, security, smallrye-context-propagation, smallrye-health, smallrye-openapi, swagger-ui, vertx]
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.260 s -- in org.box1.GreetingResourceTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.066 s -- in org.box1.aiops.mcp.McpCompatTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.004 s -- in org.box1.GreetingServiceTest
[INFO] Tests run: 9, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```
