# D-003 Load path

**Status:** decided by the agent, Phase 1.

## Decision

In-process. The load generator calls the same `IngestionPipeline.submit()` that the HTTP resource calls after it has parsed the body. That method does all validation (metric allowlist, unit, bounds, timestamp skew), the shared rate limit, the bounded producer queue and publication. Invalid chaos readings are built as raw field maps and rejected by the same validator, so they are counted as rejections, never published.

Oversize payloads cannot be expressed in-process (they are an HTTP body-size property), so the chaos entry `OVERSIZE_PAYLOAD` submits a raw serialized body through the same JSON parse and size check the resource uses, `IngestionPipeline.submitRaw(byte[])`, which enforces the same 4 KiB limit as the HTTP layer.

## Rejected

An HTTP call to itself would need a bearer token with `telemetry-writer` inside the pod, i.e. a credential this run must not create, and would put load traffic through the Route.

## Consequences

Load and chaos readings are indistinguishable from real ingestion after the validation step, except for a `source=load|chaos|api` label on metrics and a `correlationId` of `run:<runId>` in the envelope, so evidence can be tied to a run.
