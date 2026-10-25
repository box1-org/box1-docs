# Capacity and security boundaries — RTX 5090 single-node lab

**Hardware planning:** single-node OpenShift; Ryzen workstation class, **128 GB system RAM**, one **RTX 5090 / 32 GB VRAM**, NVMe-backed state. The exact CPU SKU and available storage classes must be confirmed from the cluster; don't copy any historical hardware estimate blindly.

**AI-serving reality:** Model context configuration (`--max-model-len 65536`, if supported) is not capacity proof. VRAM must hold weights, KV cache, allocator overhead and serving concurrency. Benchmark chosen Qwen checkpoint using realistic prompts and generation lengths, concurrency 1 first; allow `max_model_len` reduction to 32768 or 16384 if needed. Explicitly avoid promising 64K on every quantized model.

**App resource policy:** request conservative CPU/memory resources, validate them with measured peaks, reserve system headroom, and make platform overlays independently enableable. Keep expensive services (`operate`, `hybrid`, `ai`) off by default unless the workload requires them. Do not claim node HA or VM live migration.

**Identity boundary:** Use OpenShift/Kubernetes service accounts per workload; real user identity is validated at ingress and enforced by backend. Use Keycloak/OIDC only where installed and supported; never embed broad cluster credentials in AI tools. Private internal endpoints remain internal. All exposed Routes use TLS.

**AI policy:** External tool responses and retrieved runbooks are untrusted content. No secret injection in model prompts or tool results. Read-only, allowlisted evidence connectors by default. Any remediation command must be separately defined, authorized, explicitly approved, audited and reversible; the LLM cannot approve its own action.

**Demo controls:** Fault injection and data reset only permitted in a named demo namespace/environment with RBAC and allowlists; not via arbitrary shell execution. Persist a complete audit trail of invoked scenarios and reset actions.
