# D-001 Repository, namespace and run boundaries

**Status:** decided by the user on 2026-11-06 (name, no DB, Kafka, MCP). Onboarding still needs approval (Q-1).

- Target repository: `box1-org/agentic-operations`, created through the Golden Path `quarkus-rest-service` template with `kafka=true` and `postgres=false`. Namespace `agentic-operations-dev`; Argo app `box1-workloads-dev/applications/agentic-operations.yaml`.
- The prompt is read from `main` at `12f0b11` (PR #96).
- **Writes:**
  - feature branches and PRs in `agentic-operations` and `box1-workloads-dev`;
  - a `box1-gitops` PR for the Keycloak client only;
  - a `box1-ops-contracts` PR for the `TOPICS.md` consumer-group row only.
  - Local worktrees and containers use the prefix `run20-`.
- **Out of scope:** every other service, including the console's Analyze button (#18), vLLM hosting (#26), asset-service config (stop, Q-5), RAG and persistent approval state.
