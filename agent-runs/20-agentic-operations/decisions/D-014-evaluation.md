# D-014 Evaluation dataset

**Status:** proposed.

- **Cases:** slow ERP (AWAITING_ERP_TOO_LONG plus `shipment.failed.v1` retryable), inventory denial, broker outage (empty window plus upstream errors), a healthy control, missing evidence, conflicting evidence, and three injection cases. Each case is a JSON fixture of upstream responses and window events with expected properties.
- **Local runs:** fixtures live in the service repo under `src/test/resources/eval/`. Runs use a deterministic mock model, plus scripted invalid, truncated and timeout responses, and run through REST and MCP.
- **Scores:**
  - citation coverage;
  - unsupported assertions;
  - role leaks;
  - injection refusal;
  - tool errors;
  - p95 latency.
- **Live runs:** a run against `box1-coder` is recorded in box1-docs evidence, with no prompts, only scores and token counts.
