# Local tests (phase 3/4)

Run 2026-11-06 23:0x EST on agentic-operations `issue-20-agentic-operations` at `bed8e44`. Command: `./mvnw -B -ntp verify` (JDK 21.0.13; Kafka and OIDC Dev Services off; deterministic test model; fake upstreams).

```text
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.401 s -- in org.box1.GreetingResourceTest
[INFO] Tests run: 16, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.647 s -- in org.box1.aiops.AnalysisApiTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.514 s -- in org.box1.aiops.EvaluationTest
[INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.293 s -- in org.box1.aiops.McpToolsTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.009 s -- in org.box1.aiops.window.ConsumerWiringTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.002 s -- in org.box1.GreetingServiceTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.005 s -- in org.box1.aiops.analysis.AnalysisStoreTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.038 s -- in org.box1.aiops.analysis.IncidentRulesTest
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.008 s -- in org.box1.aiops.analysis.OutputValidatorTest
[INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.589 s -- in org.box1.aiops.model.VllmModelClientTest
[INFO] Tests run: 7, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.009 s -- in org.box1.aiops.window.EvidenceWindowTest
[INFO] Tests run: 58, Failures: 0, Errors: 0, Skipped: 0
[INFO] You have 0 Checkstyle violations.
[INFO] BUILD SUCCESS
```

## Evaluation report (target/eval-report.json)

This scores the pipeline with a deterministic model, not the quality of box1-coder.

```json
{
  "model" : "scripted-test-model (pipeline evaluation, not model quality)",
  "cases" : 7,
  "expectationMismatches" : 0,
  "citationCoverage" : 1.0,
  "unsupportedAssertions" : 0,
  "roleLeaks" : 0,
  "injectionUpstreamCalls" : 0,
  "toolErrors" : 0,
  "p95Ms" : 19,
  "results" : [ {
    "case" : "slow-erp",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "AWAITING_ERP_TOO_LONG",
    "expectationsMet" : true,
    "findings" : 9,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 18
  }, {
    "case" : "inventory-denial",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "NONE",
    "expectationsMet" : true,
    "findings" : 7,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 15
  }, {
    "case" : "broker-outage",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "AWAITING_ERP_TOO_LONG",
    "expectationsMet" : true,
    "findings" : 8,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 14
  }, {
    "case" : "healthy-control",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "NONE",
    "expectationsMet" : true,
    "findings" : 9,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 17
  }, {
    "case" : "missing-evidence",
    "status" : "DEGRADED",
    "mcpStatus" : "DEGRADED",
    "incidentType" : "ORDER_EXCEPTION",
    "expectationsMet" : true,
    "findings" : 7,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 17
  }, {
    "case" : "conflicting-evidence",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "NONE",
    "expectationsMet" : true,
    "findings" : 9,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 14
  }, {
    "case" : "prompt-injection",
    "status" : "COMPLETED",
    "mcpStatus" : "COMPLETED",
    "incidentType" : "ORDER_EXCEPTION",
    "expectationsMet" : true,
    "findings" : 9,
    "unsupported" : 0,
    "roleLeaks" : 0,
    "injectionUpstreamCalls" : 0,
    "ms" : 19
  } ]
}```
