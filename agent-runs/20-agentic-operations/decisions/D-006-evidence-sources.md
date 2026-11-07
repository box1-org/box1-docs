# D-006 Evidence sources and gathering

**Status:** proposed.

- **The model does not choose tools in v1.** For each incident type, the service gathers a fixed, bounded evidence set before calling the model. The model only reads that evidence and returns structured JSON. A completion containing tool calls is rejected as invalid output. As a result, injected text cannot cause an unsupported tool call; there is no tool loop to hijack. External MCP agents choose tools themselves, but every tool is read-only and checked for role.
- **Evidence classification** (evidence/01):
  - **available:** order and timeline; fulfillment; inventory and reservations; deployed revision from `/api/info`; the Kafka window.
  - **unavailable in v1, stated in every analysis:** telemetry alerts (until Q-5), traces and metrics (until RBAC is approved, Q-6), Argo revision, logs (#82).
- **Evidence references:** every entry gets `ref` (`ev_<n>`), `type`, `source`, `timestamp`, `retrievalStatus` (`OK`, `UNAVAILABLE`, `UNAUTHORIZED`, `ERROR`, `TIMEOUT`) and `link`.
  - `link` is a trusted identifier or an in-cluster API path, never a URL taken from evidence text.
- **Size limits:** each source is capped at `AIOPS_EVIDENCE_SOURCE_MAX_BYTES`, and the total at `AIOPS_EVIDENCE_MAX_BYTES=48KiB`. Evidence is deduplicated, newest first, and anything cut is recorded as `truncated`.
- **Runbooks:** a static allowlist of box1-docs runbook paths pinned to a commit and cited by reference only. Their text is not retrieved in v1.
