# box1 Operations — agent-ready implementation prompts

**Purpose:** An executable prompt library for generating the box1 Operations reference application with Codex or a Qwen-based agent running in NVIDIA OpenShell. box1 is the parent identity; **box1 Operations** is its first flagship application. The app models a regional industrial equipment supplier with orders, site-based inventory, asynchronous fulfillment through a legacy ERP, telemetry, notifications, an operator console, and an evidence-grounded AI assistant.

**Provenance:** Derived from the supplied *box1 Operations — Expanded Concept and Requirements* and the box1 platform progress already established. These are **proposed implementation specifications**, not claims that all repositories, operators, services, or supporting infrastructure already exist.

## First: keep the project that already works

The `box1-org` Quarkus Golden Path is already end-to-end demonstrated. Reference components are `box1-org/quarkus-reference`, `box1-org/box1-templates`, and the existing `box1-gitops` repository. The reference uses Quarkus 3, Java 21, Maven, REST, health, OpenAPI, Micrometer, tests, Jib/UBI container builds, Pipelines as Code, GitOps promotion PRs, SHA-tagged images, and Argo CD digest-based deployments. **Reuse this workflow. Never write a new deployment pipeline or apply a new application directly with Tekton as a shortcut.** The existing `orders-service` was a Golden Path demonstration: do not overwrite it without an explicit migration decision.

## Work-unit design for a nominal 64K context window

Your RTX 5090 has **32 GB VRAM**, while the selected local model may be configured with a **64K-token maximum context window**. These are different resources. A configured 64K context is **not** a guarantee that a given checkpoint can serve that context at the desired concurrency on the 5090. Benchmark actual KV-cache demand and lower max context/concurrency as needed.

A 64K token context is a **ceiling for prompt + system instructions + tool results + repository text + conversation + output**, not a target size for each Markdown manifest. Keep the prompt compact and reserve room for file reads, tests, compiler logs, reasoning, and patches. Recommended *planning allocation* per coding session (not a model guarantee):

| Context use | Suggested limit |
|---|---:|
| System and agent / OpenShell overhead | 4K |
| Shared contract + one service prompt | 6–10K |
| Existing source, exact files, targeted search results | 18–24K |
| Build/test results, logs, troubleshooting | 8–12K |
| Proposed code/diffs + final handoff | 8–12K |
| Safety margin | ≥6K |

Read **one service prompt at a time**, with only the shared files it references. Do not load the entire 16-page design document, every service prompt, and the entire repository in one agent session. Implement a **single acceptance slice per session**. New sessions get the previous handoff and current relevant files only.

## Directory layout

- `00-shared/` — non-negotiable architectural rules, event schemas, GitOps conventions, acceptance policy, and handoff pattern.
- `01-services/` — independent prompts for each deployable business component.
- `02-platform/` — independent prompts for the platform workstreams those services require.
- `manifest.json` — machine-readable prompt index, dependencies and suggested order.

## Suggested start order

1. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, and `02_REPO_AND_GITOPS_CONVENTIONS.md`.
2. Use `02-platform/01_contracts_and_data_foundation.md` to create versioned contracts and persistent infrastructure design.
3. Implement `01-services/01_order_service.md`, then `02_inventory_service.md`, then `03_fulfillment_adapter.md` against a **deterministic ERP stub**.
4. Implement `01-services/08_operator_console.md` (and `07_experience_bff.md` if needed) so the order lifecycle is visible.
5. Add the rest in dependency order, enabling platform profiles only when required and supported.

## Agent invocation template

> You are implementing **box1 Operations**, using the attached service prompt. Respect `00_AGENT_CONTRACT.md` and the linked domain contracts. First inspect the relevant repository, identify the next *unmet* acceptance criterion, and propose a concise implementation plan. Then implement one scoped slice with tests, invoke the existing Golden Path, and report exact evidence. Do not invent cluster compatibility, CI status, or available credentials. Do not change unrelated services. Keep the full interaction within a nominal 64K context budget. If you hit a blocker, leave a clear handoff instead of guessing.

## Repository approach

**Default:** service-per-repo using the existing Developer Hub Quarkus template, plus a shared contracts repository and the established `box1-gitops` deployment repository. Names in this pack such as `box1-org/box1-ops-order` are **proposals**, not verified existing repositories. If reality differs, adapt paths without deleting validated assets. A monorepo is possible but must be an explicit decision; do not silently diverge from the demonstrated service-per-repo Golden Path.

## Definition of success

An order is placed once, reserves stock once, enters an event-driven fulfillment path, survives broker/ERP outages, and becomes observable from an operator's browser to a log, metric, trace, event, and Git SHA. AI is read-only by default and cites actual evidence. All changes reach OpenShift through reviewed GitOps state. No claim of high availability on single-node OpenShift.
