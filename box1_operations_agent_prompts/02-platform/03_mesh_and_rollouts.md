# Platform 03 — Service mesh, network policy and canary releases


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. These prompts target agents with a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`.

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA.


**Requirements:** PLT-04/05; NFR-01/05; DEMO-A3

**Dependencies:** Working Core services, measured observability and verified mesh version/CRDs.

## Mission

Prove identity-aware communication and safe change—not a decorative Istio dashboard. Introduce service mesh on **one** business path first (`bff → order` or `adapter → ERP`) and scale only after real compatibility and resource data.

## Implementation scope and guardrails

- Detect current OpenShift release/operator, supported Service Mesh mode and API schema (sidecar vs ambient only after validation); collect initial CPU/memory costs and avoid unsupported custom resources.
- Select explicit namespace onboarding/workload enrollment, service accounts and least-privilege east-west authorization. Add mTLS only to paths demonstrated to work; avoid unintentional breakage of non-mesh peers, probes, metrics or service discovery.
- Canary exercise: emit stable revision labels/digests from GitOps, route a bounded share of traffic to a faulty order/BFF/adapter revision, check API errors/latency AND business failure rate, then abort and GitOps rollback. Split routing policy is declarative and reviewed; no uncontrolled operator UI patching.
- Define retry ownership to prevent multiplication: app retries only where idempotency present; mesh timeout/retry policies do not multiply ERP side effects.
- Baseline network policy on sensitive DB/Kafka and ERP paths where available; deny all is incremental and verified to avoid breaking platform webhooks/DNS/monitoring.
- Alert and runbook link the route policy, deployed digest, trace span, and objective abort threshold. Explicitly state that one node cannot deliver failure-domain HA.

## Verifiable acceptance evidence

- HTTP service path works before enrollment, during mesh protection, and after rollback; mTLS is actually negotiated/measurable.
- Unauthorized service identity receives a deny response; authorized BFF succeeds.
- Canary regression crosses an objective threshold and resulting GitOps rollback results in improved observed metric; actual PR, digest and config state recorded.
- ERP replay under injected network resets does not duplicate shipments due to app-level idempotency.

## Nominal 64K-context implementation slices

1. Compatibility/capacity inventory and supported mesh-mode choice.
2. mTLS/authorization on one service path with tests.
3. Fault injection, retries/timeouts, trace verification.
4. Canary policy and abort condition with GitOps rollback proof.

## Final handoff

List actual repositories/paths/CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs/commits if actually created, blocked dependencies, resource impact, rollback plan and one next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified.
