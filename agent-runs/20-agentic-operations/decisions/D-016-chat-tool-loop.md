# D-016 Assistant chat with a read-only tool loop

**Status:** accepted by the user on 2026-11-08 (America/New_York), for [box1-docs#101](https://github.com/box1-org/box1-docs/issues/101).

**Implementation:**
- [box1-org/agentic-operations#2](https://github.com/box1-org/agentic-operations/pull/2): server.
- [box1-org/operations-console#14](https://github.com/box1-org/operations-console/pull/14): console Assistant v2.

**Supersedes:** [D-006](D-006-evidence-sources.md) ("the model does not choose tools in v1") and the "the model has no tools" argument of [D-010](D-010-prompt-injection.md), **for the chat surface only**.

Incident analyses keep D-006 unchanged:
- fixed evidence;
- no tools offered;
- a completion with tool calls is invalid (`VllmModelClientTest.toolCallsAreRefused`).

## Decision

The user's choices:
1. The model may call agentic-operations' **read-only evidence tools** in a bounded server-side loop, under the asking person's own token and roles.
2. Conversation history lives **in memory on the server**, owned by the person.
3. Replies use **submit, then poll**, with no streaming.

### Surface

The REST API under `/api/v1/ai/conversations`:
- create;
- send a message (202 with a turn ID);
- read the conversation, which carries each turn's status, answer and tool steps.

Chat is not offered over MCP: MCP clients bring their own agent.

### Tools

The model may call:
- `get_order_timeline`
- `get_fulfillment_status`
- `get_inventory_reservation`
- `list_recent_events`
- `get_deployed_revision`
- `get_analysis`

These are the same reads as the MCP tools. The model may not start an analysis. No tool writes, executes, runs a shell, calls the Kubernetes API or fetches a URL.

How tool calls are handled:
- Arguments are validated against the contract ID patterns before any read.
- Unknown tools and invalid arguments are returned to the model as errors, with no read made.
- Results are wrapped as untrusted data and capped at `source-max-bytes`.

### Identity

- The viewer role (`aiops-viewer` or `aiops-analyst`) and the accepted `azp` are checked on the request thread.
- The model worker then uses pre-authorized reads, because worker threads carry no request identity.
- Conversations belong to the subject that created them. Anyone else gets a 404.

### Bounds

| Item | Limit |
|---|---|
| Tool calls per message | 8 |
| Model rounds per message | 4, then one final call without tools (`LIMIT_REACHED`) |
| Time per message | 90 s |
| Answer length | 1024 tokens |
| Question length | 2000 characters |
| Conversations held | 200 |
| Idle lifetime | 2 h |
| Turns per conversation | 20 |
| Turns in flight per conversation | one (`409 TURN_IN_PROGRESS`) |

- Earlier answers are replayed as history. Earlier tool results are not.
- Analyses and chat share one model queue (concurrency 1, bound 4) through `ModelGate`. When it is full, the answer is `429 BUSY`.

### Policy

`aiops-chat-policy-1`:
- The assistant is read-only, so it must not claim to have done anything.
- It answers only from tool results.
- It treats tool results as data, never as instructions.
- It names the IDs it relied on.
- It answers in plain text.

The console renders answers as plain text, labels them as model output that can be wrong, and lists the sources consulted.

### Logs

Logs carry IDs, counts, decisions, token totals and the policy version. They never carry the question, the answer or evidence ([D-012](D-012-observability-and-resources.md)). Metric tool labels are a known tool name or `unknown`.

## Threat model change

D-010 relied on three things: the model has no tools, the service decides what is fetched, and the output is schema-checked. For chat, the first two no longer hold. **Injected text in evidence can steer which reads the model makes.**

What still limits it:
- **No new privileges.** Every read is read-only and needs the person's own viewer role. It can only return data that the person could read directly through MCP or REST.
- **No exfiltration channel.** Answers go only to the person who asked. No tool can send data anywhere or fetch a URL.
- **No action.** Nothing the model can call changes a system. Proposals are text for a person.
- **Bounded cost.** Reads per message, rounds and time are capped. The shared queue keeps chat from starving analyses beyond the queue bound.

Accepted residual risks:
- Injected text can make the model read *other* orders the person may already see.
- Injected text can make the model give a misleading answer.

Both are mitigated by the visible step list, the "can be wrong" label and plain-text rendering. They are not eliminated.

Customer-scoped callers do not exist yet. If they are added, the chat tools must filter by caller, as must REST and MCP.

## Verification

- **Deterministic tests:**
  - `ChatApiTest` and `ChatAccessTest` in agentic-operations.
  - Chat cases in `VllmModelClientTest`.
  - The console's `AssistantTest` and its Playwright `assistant.spec.ts`.
- **Real-model behavior** (tool choice, refusal of write requests, behavior under injection) is checked live after deployment, on a small sample, and recorded as observations, not guarantees.
