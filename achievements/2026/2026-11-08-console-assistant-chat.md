# Operations console Assistant: a chat bot over agentic-operations

**Date:** 2026-11-06 to 2026-11-08 (America/New_York)

**Backlog:** [box1-docs#101](https://github.com/box1-org/box1-docs/issues/101)

**Status:** Delivered and live-verified, with the following limits:
- The real model was checked on a single conversation, with the results observed directly.
- Untested live: injection through real evidence, the refusal for a user with no aiops role, the agentic-operations audit subject, and `/analyze` against a real incident.

## Outcome

The operations console has an **Assistant** page that is a real chat bot. Operators ask questions in plain words. agentic-operations' model (`box1-coder` on vLLM) answers by reading box1 through **read-only tools**, under the asking person's own token and roles. It cannot change anything.

- **Each answer** shows the tool steps it took ("Read order timeline · `ord_…` · OK"). It is rendered as plain text, carries the label "Answers come from a model and can be wrong; check the sources", and lists its sources.
- **Slash commands** keep the deterministic actions: `/incidents`, `/analyze <id>` (an evidence-grounded incident analysis), `/show <ana_…>`, `/new`, `/clear` and `/help`.

It was delivered in two steps on the same backlog issue:
- **v1 (2026-11-06/07):** a deterministic command bot over the existing analyze-and-poll API.
- **v2 (2026-11-08):** free-form chat with a bounded tool loop. This required decision **D-016**.

```text
operations-console  e2cdd4b (v2, live 2026-11-08); now 2a4035e, image sha256:ba8724c5…79f519 (later unrelated changes)
agentic-operations  b458ffe (chat API, live 2026-11-08); now 8ad728e, image sha256:fe9f3ed5…fa1631
keycloak client     box1-gitops 0a429ef (operations-console: agentic-operations audience, aiops-* scope)
runtime env         box1-workloads-dev efad7d9 (AIOPS_ALLOWED_AZP, AGENTIC_OPERATIONS_URL, CONSOLE_AIOPS_FORWARD_TOKEN)
decision            box1-docs 7706f1b (agent-runs/20-agentic-operations/decisions/D-016-chat-tool-loop.md)
```

## Starting baseline

- **agentic-operations** ([#20](https://github.com/box1-org/box1-docs/issues/20), [delivery log](2026-11-07-agentic-operations-delivery.md)) offered two REST calls: analyze an incident, and get an analysis. It also offered MCP tools. It had no chat endpoint.
  - Its model client offered no tools and rejected any tool call (D-006).
  - It accepted only `azp=agentic-operations-cli`.
- **The console** had no link to agentic-operations. Its `operations-console` Keycloak client carried no agentic-operations audience or aiops roles.
- **CSP:** the console's Content-Security-Policy (`connect-src 'self'`) means the browser can reach agentic-operations only through a console API.

## What changed

**User decisions.**
- **v1 (2026-11-06):** console-only and deterministic, with the user's own token forwarded.
- **v2 (2026-11-08):** a read-only tool loop, conversation history kept in memory on the server, and submit-then-poll.

| Repository | PR | Merge | Change |
|---|---|---|---|
| `box1-gitops` | [#103](https://github.com/box1-org/box1-gitops/pull/103) | `0a429ef` | `operations-console` client: an `agentic-operations` audience mapper, and a scope mapping for only `aiops-viewer` and `aiops-analyst` (`fullScopeAllowed` stays false). |
| `box1-workloads-dev` | [#155](https://github.com/box1-org/box1-workloads-dev/pull/155) | `efad7d9` | agentic-operations: `AIOPS_ALLOWED_AZP=agentic-operations-cli,operations-console`. Console: `AGENTIC_OPERATIONS_URL` and `CONSOLE_AIOPS_FORWARD_TOKEN=true`. |
| `operations-console` | [#11](https://github.com/box1-org/operations-console/pull/11) | `d13eebc` | v1 Assistant. A new `agentic-operations` source and an `AiopsToken` that sends the token to that service only. Three proxy endpoints. Analysis view: suggested actions are labelled "Proposed only — never executed", and raw evidence `data` is dropped. Polling is capped. |
| `operations-console` | [#13](https://github.com/box1-org/operations-console/pull/13) | `07b6984` | **Live bug fix.** Two `useEffect` callbacks returned `scrollIntoView(...)`, which is a Promise in Chromium. React then called it as a cleanup function and the page crashed ("l is not a function"). Firefox returns `undefined`, so the Firefox-only end-to-end tests missed it. Also: stop polling an analysis that returns 4xx. |
| `agentic-operations` | [#2](https://github.com/box1-org/agentic-operations/pull/2) | `b458ffe` | v2 chat API, detailed below. |
| `operations-console` | [#14](https://github.com/box1-org/operations-console/pull/14) | `e2cdd4b` | v2 Assistant, detailed below. |
| `box1-docs` | [#108](https://github.com/box1-org/box1-docs/pull/108) | `7706f1b` | Decision D-016. |
| `box1-workloads-dev` | #156, #157, #159, #160 | auto | Pipeline promotions. |

**agentic-operations#2, the v2 chat API**
- **Model client:** `ModelClient.chat` sends message history and offers tools. Analyses keep `complete()`, which still refuses tool calls.
- **Shared queue:** `ModelGate` is one model queue for analyses and chat: concurrency 1, matching vLLM `--max-num-seqs 1`, with a bound of 4 and `429 BUSY` when full.
- **Tools** (`ChatTools`):
  - `get_order_timeline`
  - `get_fulfillment_status`
  - `get_inventory_reservation`
  - `list_recent_events`
  - `get_deployed_revision`
  - `get_analysis`

  Every ID is validated before any read. Results are wrapped as untrusted and size-capped. Unknown tools and bad arguments are returned to the model as errors, and nothing is read.
- **Conversations:** each is owned by its creator; anyone else gets 404. Limits:
  - 200 conversations, forgotten after 2 h idle, and 20 turns each;
  - one message in flight per conversation (`409 TURN_IN_PROGRESS`);
  - 8 tool calls, 4 model rounds and 90 s per message, then a final answer without tools (`LIMIT_REACHED`).
- **Logs** carry IDs, counts and decisions, never questions, answers or evidence.

**operations-console#14, the v2 Assistant**
- Three proxy routes for conversations.
- The page polls each turn and shows its steps live.
- Answers are plain text with a disclaimer and a "Sources consulted" list.
- An expired conversation is replaced automatically, with a note.
- `Upstreams` now keeps a 4xx problem's `code`, which separates `TURN_IN_PROGRESS` from `CONVERSATION_FULL`.

**Tradeoff (D-016).** The model now chooses which reads to make, so injected text in evidence can steer them. Every read is still:
- read-only;
- validated;
- capped per message;
- limited to what the person may already read.

Answers go only to that person, and no tool can send data anywhere. The residual risk, misleading answers or extra reads of orders the person can already see, is reduced by the visible step list, plain-text rendering and the "can be wrong" label. It is not removed.

## Validation and evidence

**Local tests**

- **v1:**
  - Console: `./mvnw verify` passed 79 tests. Playwright on Firefox passed 22 tests, including the a11y/CSP scan of `/assistant`.
  - One spec failed first on an ambiguous locator; it was fixed and the spec re-run.
- **v2, agentic-operations:** `./mvnw verify` passed 87 tests.
  - `ChatApiTest`, 10 tests:
    - tool read then answer;
    - history excludes earlier tool results;
    - unknown, write-like and invalid calls make no read;
    - the budget ends in a final answer offered no tools;
    - model down and truncated output;
    - 409 while a turn runs;
    - the queue is shared with analyses;
    - logs contain no content.
  - `ChatAccessTest`, 5 tests: owner only, anonymous, no role, and unaccepted client.
  - 3 new chat tests in `VllmModelClientTest`.
- **v2, console:** `./mvnw verify` passed 84 tests. Playwright on Firefox passed 23 tests, including a populated transcript scanned with axe in light and dark.

**Live checks**

| Check | Expected | Observed |
|---|---|---|
| Deployed revisions | Merge SHAs | `/api/info`: console `d13eebc`, then `07b6984`, then `e2cdd4b`; agentic-operations `b458ffe`. Promotions #156, #157, #159 and #160 merged. |
| Keycloak mapping | Console token carries the aiops roles | `GET /api/v1/assistant` for the signed-in user returned `configured: true`, `canAnalyze: true`, roles `[aiops-analyst, aiops-viewer]`. |
| Anonymous access | 401 | Console `/api/v1/assistant` returned 401 `SESSION_REQUIRED`. agentic-operations `POST /api/v1/ai/conversations` returned 401. |
| v1 crash, in the browser pane (Chromium) | Page keeps working | Before #13, `show <expired id>` followed by any message crashed the page. After #13, the new bundle ran 99 s, fetched the expired analysis once, and stayed usable. |
| Real model: "Why was ord_bc54…4 rejected?" | Grounded answer from tool reads | COMPLETED in 9.2 s: 4 reads, 3 model calls, 5258 prompt / 567 completion tokens. It reported `SITE_UNAVAILABLE` from `inventory.rejected.v1`, matching the timeline, and named the order, event and correlation IDs. |
| "make it so" | Refusal; nothing executed | "I can't do that — I'm read-only…"; it offered reads instead. |
| "no i mean look it up" | Reads, honest about limits | Read the deployed revisions of 2 services and the events for the correlation ID. It said an empty event window is not conclusive. |
| "what were the last successful orders" | Admits it has no list tool | Said it can only look up specific order IDs and did not invent orders. |

**Observation, then fixed.** In the first answer the model stated two `UNAVAILABLE` reads as confirmed absence. It said inventory "confirms" there is no reservation and the adapter "has no fulfillment record". Chat policy `aiops-chat-policy-2` in [agentic-operations#6](https://github.com/box1-org/agentic-operations/pull/6) now says only an `OK` read counts as checked. See [the observability evidence log](2026-11-08-agentic-operations-observability-evidence.md). Whether the real model follows the new wording was not re-tested.

**Not verified live:**
- prompt injection through real evidence;
- refusal for a console user without aiops roles (covered by local tests);
- the agentic-operations audit subject (no `oc` access at the time);
- `/analyze` against a real incident, because there was no active incident and starting a scenario was not authorized.

## Final operational state

- **operations-console** (Argo CD, `box1-workloads-dev`): forwards the person's token to agentic-operations, scenario-controller and asset-service only. It now runs `2a4035e`, which includes later, unrelated changes on top of this work.
- **agentic-operations** (Argo CD): accepts `azp` `agentic-operations-cli` and `operations-console`, and serves analyses and chat. Conversations and analyses are in memory, run on one replica, and are lost on restart, by design. It now runs `8ad728e`, which adds Dev Spaces files.
- **Keycloak** (`keycloak` Argo CD app): the `operations-console` client carries the `agentic-operations` audience and the `aiops-*` roles. The roles are assigned to people in the Keycloak admin console, not in Git.

## Recovery and follow-ups

**Turn off the Assistant**
1. Set `CONSOLE_AIOPS_FORWARD_TOKEN` to `"false"` in `workloads/operations-console/deployment.yaml`. The page then shows "not connected".
2. To refuse the console entirely, remove `operations-console` from `AIOPS_ALLOWED_AZP`, and remove the audience mapper and scope mapping from `operations-console-client.yaml`.
3. To return to the command-only bot, revert operations-console#14 and agentic-operations#2.

None of these was exercised.

**Follow-ups**
- [#79](https://github.com/box1-org/box1-docs/issues/79): a confidential console client.
- [#97](https://github.com/box1-org/box1-docs/issues/97): durable analyses and conversations.
- An order list/search tool: the model cannot answer "last successful orders". This needs its own decision.
- Streaming answers.
- A live prompt-injection probe.
