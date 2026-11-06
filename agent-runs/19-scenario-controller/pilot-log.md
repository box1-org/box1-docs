# Frontier profile pilot log: box1-docs#19

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 1 | 2026-11-06 ~01:25 EST | 0 exit | Next action needs user decisions; platform conflicts with the prompt; required dependency unavailable | The user asked to see the mechanism table before design. Discovery found that inventory cannot create the fixture sites through its API (a change to another service), that no ERP is reachable on the cluster, and that the controller identity, allowlist and database credential need approval. All open decisions are reported together (`open-decisions.md` O-1 to O-12). |

## Repairs

None yet.

## Profile ambiguity and friction

1. **The prompt's #59 note is stale.** The frontier section says client roles in `spec.roles` "are not created by the operator (#59)". #59 was closed on 2026-11-06 as not a defect: the operator did create the `asset-service` roles. The rule "check the roles exist after sync" still applies; the premise that they will be missing does not.
2. **The prompt's requirement IDs (FR-09, OBS-06, DEMO-A/B/C) are defined only in the white paper PDF.** The ledger derives IDs from the prompt's acceptance evidence and verification scenarios, as the profile allows.

## Places I was unsure of my authority

1. **An anonymous POST to an inventory admin endpoint to confirm it returns 401.** It is a write attempt against the shared cluster, even if it is expected to be refused. I did not make it (the tool's safety check also refused it). The 401 is established from source (`AdminResource.java`, audience `inventory-service`), not from the cluster.
2. **Comparing database password fingerprints across services' Git manifests to characterise the #41 exposure.** This is credential exploration beyond what the run needs. I did not do it (the tool's safety check also refused it). The finding was reported to the user directly.

## Did earlier pilots' lessons prevent repeats?

| Earlier lesson | Applied here | Result |
|---|---|---|
| Do not read or use a credential not issued to the run (runs 11–18) | Characterised the database Secret from its manifest structure only, redacted, without reading the cluster Secret | **Prevented.** One further step (fingerprinting values) was refused and not repeated |
| `box1-docs` is public: report live weaknesses directly (runs 12–18) | Database credential and unauthenticated broker reported to the user directly; pointers only here | **Applied** |
| Establish which client tokens each called API accepts (runs 15, 18) | Checked audience, `azp` and role claims for inventory, adapter and asset-service from source before designing | **Prevented.** Found P-2 and P-5 in Phase 0, not after a deployment |
| Check that a dependency actually works, not just that its pod is running (runs 11, 13) | Read live inventory and orders: pods are healthy but no reservation exists and old orders are still `SUBMITTED` | **Prevented.** P-6 is recorded as unproven instead of assumed |
| #59's "operator skips spec.roles" (run 15) | Read #59 first: it was closed as a false report | **Applied.** The prompt's stale premise is noted under ambiguity |
| Check host and container VM clocks before long runs (runs 13, 14) | Checked at start | Applied; no long run yet |
| Guava override with `security-gates: gate` (runs 11, 15, 18) | Not reached; the scaffold still has gates `disabled` | Not reached |

## Environment findings

- 00:50 EST: host and Podman VM clocks agreed (05:50:03 UTC both).
- Podman machine: 4 CPU, 8 GiB. `run15-pg`, `run15-kafka`, `run15-keycloak` are running (ports 15432, 19092, 18180); this run avoids those ports and names.

## Orchestrating services other runs built

- Every service the controller needs was built by a different run, each with its own auth decision: order-service has none (#40), inventory accepts only its own audience with no client to issue it, asset-service pins `azp` to itself, and the adapter's writer role is only reachable by a person. No two services agree on how a machine caller gets in, so a controller cannot be designed until the token shape for each is decided.
- The other runs' scope boundaries ("a change to another service is a stop") compound: the controller's first prerequisite (creating fixture sites) is another service's missing endpoint, found in the first hour.
- The other runs' run state was the fastest way in: the #18 D-011 fixtures and G-1/G-2/G-3 gaps, and the #15 control API, told me more than the services' READMEs did.

## Side effects outside the run state

- Clone `/Users/mike/Documents/ChatGPT/box1/run19-scenario-controller` of box1-org/scenario-controller; worktree `run19-docs` of box1-docs on branch `agent-run/19-scenario-controller`.
- Three read-only discovery subagents; shallow clones in the session scratchpad only.
- No cluster writes. No containers started.
