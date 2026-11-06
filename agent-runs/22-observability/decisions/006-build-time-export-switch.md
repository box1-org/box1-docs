# 006 Build-time exporter, run-time switch

**Problem:** in Quarkus 3.40, `quarkus.otel.traces.exporter` and `quarkus.otel.traces.sampler` are fixed at build time. The images were built with exporter `none`.

**Decision:** each service builds with `quarkus.otel.traces.exporter=cdi`, `quarkus.otel.traces.sampler=traceidratio` and `quarkus.otel.traces.sampler.arg=0.0`. The run-time `samplerArg` is the on/off switch and the sampling ratio. `%dev` and `%test` keep `none` and `parentbased_always_on`.

**Why not `quarkus.otel.sdk.disabled`:** a disabled SDK produces invalid span contexts. The services build envelope `traceparent` from `Span.current()`, so correlation would break.

**Consequences:**
- Trace flags are `00` while export is off.
- `traceidratio` ignores the parent's sampled flag, but every service makes the same decision for a given trace ID, so partial ratios still yield whole traces.
- Supersedes the env-only export in decision 003.
