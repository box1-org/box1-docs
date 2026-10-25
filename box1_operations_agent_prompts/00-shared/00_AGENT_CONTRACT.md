# Agent contract — apply to every box1 Operations workstream

You are an implementation agent in `box1-org`. **One prompt = one bounded unit of work**. Preserve working systems.

## Immutable rules

1. **Inspect before editing.** Identify current repo, active branch, existing files/tests, Golden Path setup, and GitOps onboarding status. Never assume the proposed repo already exists.
2. **Existing validated platform is authoritative.** Use Developer Hub / Quarkus reference and existing Pipelines as Code → immutable container image → GitOps promotion PR → Argo CD deployment flow. Do not duplicate GitHub Apps, Tekton Pipelines, or Argo CD installation.
3. **No live-secret leakage.** No tokens, passwords, kubeconfigs, admin credentials, private customer data, or generated secret values in source, logs, prompts, or final handoffs. Use declarative secret references and document required provisioning.
4. **No arbitrary cluster mutations.** Source and PR first. Do not install operators, overwrite shared infrastructure, or directly modify protected environment resources unless explicitly authorized. Explicitly distinguish generated manifests from applied changes.
5. **Platform reality:** single-node OpenShift prerelease lab; 128 GB host RAM and one RTX 5090 with 32 GB VRAM. Run P0 workloads with conservative resource requests/limits, test operator API availability before authoring CRs, and do not claim HA/live migration.
6. **Primary application stack:** Quarkus 3, Java 21, Maven, PostgreSQL, Kafka/Reactive Messaging where appropriate; REST/OpenAPI and health checks. The front end may use TypeScript/React. Do not introduce another language/runtime without a concrete benefit.
7. **Business integrity:** request idempotency, durable outbox where business writes produce events, replay-safe consumers, bounded retries, dead-letter handling, and explicit reconciliation. Do not claim end-to-end exactly-once delivery.
8. **Observable by design:** structured JSON logs (without PII/secrets), correlation ID, W3C `traceparent`, OpenTelemetry-compatible spans, and business metrics; instrument HTTP and async boundaries.
9. **Supply-chain safety:** maintain existing test/checkstyle/SpotBugs/FindSecBugs gates and immutable GitOps promotion pattern; extend gates only in the dedicated supply-chain prompt.
10. **Do not silently broaden scope.** Avoid unrequested infra installation, schema rewrites, unrelated refactors, data wipes, destructive test fixtures, or changing the validated `orders-service` Golden Path demo.

## Output contract for every coding session

- **Inspection:** what exists / what was assumed / what is missing.
- **Slice:** one bounded deliverable with mapped requirement IDs and explicit exclusions.
- **Changes:** exact files and API/event/schema changes, plus any PR and commit links if *actually created*.
- **Evidence:** commands run and their real outcomes (tests, CI, deploy, API output, trace/log links when available). Do not claim tests passed if not executed.
- **Risk/rollback:** known risks, reversible migrations and deployment recovery.
- **Next slice:** smallest useful follow-up, recorded using `05_HANDOFF_TEMPLATE.md`.

## Stop-and-report triggers

- Required APIs/operators absent or incompatible with installed prerelease OCP.
- Secrets, permissions or external services unavailable.
- A spec conflicts with deployed code or another service's contract.
- An integration requires deleting persistent state or touching unrelated namespaces.
- Context usage approaches the 64K model limit: summarize state and stop at a clean checkpoint.

## Completion criteria

At minimum: source compiles, tests cover success and negative paths, API and event contract artifacts match implementation, health/readiness probes work, resource/secret/config documentation exists, and a fresh consumer can follow the README. Deployment is complete only after the established GitOps/Argo path reports success.
