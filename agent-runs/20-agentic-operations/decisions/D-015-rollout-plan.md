# D-015 Rollout plan and approval order

**Status:** proposed.

1. The user onboards `agentic-operations` (Q-1).
2. Implementation on branch `issue-20-agentic-operations` (D-004 version check first), with local tests.
3. The contracts PR (D-013) and the box1-gitops Keycloak PR (D-005) are opened and merged with approval. Roles are checked in issued tokens.
4. A box1-workloads-dev runtime PR adds the environment, ServiceMonitor, PrometheusRule and the OIDC client secret reference. Copying the secret is the user's step.
5. Merge the service PR, then the release pipeline and promotion. Check the digest against Argo and the pod.
6. Live acceptance after approval: `erp-delayed-processing` through the scenario controller, then analysis through REST and an MCP client, then a model-down check. The model-down check needs approval to scale `vllm-test`; otherwise it is proven by pointing a config at an unreachable URL in a local or CI test only.

**Rollback:** delete the Argo app through a GitOps PR. The service holds no state.
