# Phase 6: platform PRs

Opened 2026-11-07 00:0x EST. All four are linked from agentic-operations#1. **None is merged.** Merging each needs the user's approval.

| Order | PR | Branch / commit | What merging deploys | Checks |
|---|---|---|---|---|
| 1 | [box1-ops-contracts#13](https://github.com/box1-org/box1-ops-contracts/pull/13) | `run20-agentic-operations-group` | Nothing. `TOPICS.md` renames `ai-operations` to `agentic-operations` on telemetry, adds the group to the order, inventory, fulfillment and notification topics, and adds a "Read-only consumer groups" section | No checks configured; mergeable |
| 2 | [box1-gitops#99](https://github.com/box1-org/box1-gitops/pull/99) | `run20-agentic-operations-keycloak` | KeycloakClients `agentic-operations` (bearer-only, roles `aiops-viewer` and `aiops-analyst`, preset internal ID `e7f3076c-02cd-405f-a148-3e4e0c2307b9`, sync wave 3) and `agentic-operations-cli` (public, PKCE or device grant, audience mapper, role scope mapping, wave 4) | onboarding-plugin-guard and phase1-smoke pass |
| 3 | [box1-workloads-dev#153](https://github.com/box1-org/box1-workloads-dev/pull/153) | `run20-agentic-operations-runtime` | Recreate strategy; Deployment `env` (OTel, OIDC issuer, azp, consumer group, in-cluster vLLM, upstream URLs; all equal to the code defaults); ServiceMonitor; PrometheusRule (`Box1ServiceDown`, `AiopsModelUnavailable`, `AiopsWindowSeekFailed`, `AiopsKafkaRecordsSkipped`) | gitops-validate and phase1-smoke pass; `oc kustomize` builds; `oc apply --dry-run=server` accepts the rule |
| 4 | [agentic-operations#1](https://github.com/box1-org/agentic-operations/pull/1) | `issue-20-agentic-operations` at `0cf2604` | Release build and dev promotion of the service | validate pass (69 tests and 5 ITs) |

Not verified: whether the RH-SSO operator honours the preset `client.id` on create (the CRD documents the field). To check after the sync: the roles exist, the CLI scope mapping is applied, and an issued token carries `aud`, `azp` and the role. Role assignment to people is the user's step.
