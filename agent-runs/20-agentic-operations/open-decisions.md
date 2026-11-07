# Open decisions for the user (#20)

Updated 2026-11-06 22:30 EST, at the exit of phase 1. Each item is an approval or a product decision under the frontier profile's authority table. Approving one does not carry over to the others.

| # | Decision | Agent's recommendation | Blocks |
|---|---|---|---|
| Q-1 | Onboard `agentic-operations` through the Golden Path (`quarkus-rest-service`, `kafka=true`, `postgres=false`). This creates the repo and merges and deploys the GitOps onboarding. | The user runs it in Developer Hub, as for #16 | Phase 3 |
| Q-2 | MCP extension version: stable 2.0.4 is built on Quarkus 3.33; 2.1.0.Beta1 is built on 3.40.1. | Try 2.0.4 first. Ask before switching to the beta. | Phase 3 (only if 2.0.4 fails) |
| Q-3 | Use the in-cluster vLLM (`vllm-test-2.vllm.svc:8000`, `box1-coder`) before #26 secures it. Separately: the public route answered an anonymous `GET /v1/models` with 200. | Use the in-cluster Service now. Record the anonymous route on #26 and remove or protect it there. | Phase 7 (local tests use a mock) |
| Q-4 | Operator-only v1: there is no customer identity, so customer tokens are refused and customer-scoped access is a follow-up. | Confirm | Design (D-005) |
| Q-5 | Keycloak `agentic-operations` and `agentic-operations-cli` clients (box1-gitops PR). Telemetry alerts would also need an asset-service change (`ASSET_READ_CLIENTS` plus a scope mapping), which is another service's config. | Approve the Keycloak PR. Keep telemetry alerts `UNAVAILABLE` in v1 unless you approve the asset-service change. | Phase 6 |
| Q-6 | Tempo (`box1-traces-read-dev`) and Thanos/Alertmanager read RBAC for the service account | Defer: traces and metrics are `UNAVAILABLE` in v1, and a follow-up issue covers them | AC1's trace/alert reference |
| Q-7 | The contracts PR: rename the reserved `ai-operations` group to `agentic-operations` and add it to four topics | Approve when opened | Phase 2 |
