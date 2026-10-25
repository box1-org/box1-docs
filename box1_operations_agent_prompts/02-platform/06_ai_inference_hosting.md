# Platform 06 — Qwen/vLLM inference and resource-aware model serving


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** AI-01/07/08; PLT-03/06; NFR-07

**Dependencies:** Existing vLLM/Qwen experimentation, single NVIDIA RTX 5090 and AI Operations client contract.

## Mission

Provide a **replaceable** OpenAI-compatible inference endpoint for box1 Operations, balancing response quality, evidence-based diagnosis and single-GPU capacity. This is infrastructure hosting; don't embed incident reasoning business logic here.

## Implementation scope and guardrails

- Inventory real device VRAM, NVIDIA driver/runtime, OpenShift GPU operator compatibility, installed OpenShift AI/KServe/vLLM availability and existing server deployment. Do not assume the latest checkpoint or requested context is compatible without actual warm-load tests.
- Model strategy: use a smaller responsive Qwen baseline for agent/tool correctness and a quantized ~20–30B quality comparison when headroom allows. Record exact model ID, revision, quantization and license; choose checkpoint after local measurements.
- Nominal **64K max context** (`max_model_len=65536` if supported) is a *requested profile*, not a promise. Benchmark GPU allocation for weights + KV cache + runtime, concurrency=1 then increase carefully. Provide fallback profiles 32768 and 16384 tokens; do not conflate 64K tokens with 64 GB VRAM (5090 has 32 GB).
- External secret refs for image registries / model downloads; scoped TLS/OIDC/access to inference endpoint. Prefer internal Service for AI Operations; only route vLLM publicly if a bounded authenticated need is documented.
- Set request/limit, GPU request, readiness/startup probes, max seqs, length policy, request timeouts, telemetry for token count and latency, rate limiting and no prompt/token secrets logged.
- Compatibility matrix for current prerelease OCP and NVIDIA/vLLM images, with pinned known-good versions and a rollback. No operator install from a service prompt.
- Provide an OpenAI-compatible smoke test, bounded synthetic tool-call eval and comparison: latency, first-token time, completions/sec, memory usage, grounding success and invalid JSON/tool-call rate.
- Enable `ai` profile independently from Core; if unavailable, AI Operations returns clean degraded state rather than blocking order flow.

## Verifiable acceptance evidence

- Model endpoint returns valid chat/completions response and health probe; actual checkpoint revision captured.
- 16K/32K/64K context tested as candidates, with observed OOM/latency/concurrency data; unsupported 64K is documented, never represented as validated.
- Qwen can produce structured bounded JSON response or AI service handles malformed output safely.
- Stopping inference leaves order, inventory and fulfillment healthy.
- Logs redact prompts and keys; throughput and VRAM graphs are available for the demo.

## Nominal 64K-context implementation slices

1. Capture model/GPU/operator compatibility and existing deployment without editing.
2. Implement smallest stable model profile + authenticated internal API.
3. Quantized comparison, measure context profiles and VRAM.
4. Telemetry, error/malformed-output safety and GitOps opt-in deployment.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
