# Review pass: Messaging (architecture subagent)

**Not applicable, with evidence.** There is no Kafka, Reactive Messaging, outbox, `@Incoming`/`@Outgoing` or `Emitter` anywhere. All integration is synchronous HTTP through `Upstreams`, with no retries and no consumers.

Findings: none.
