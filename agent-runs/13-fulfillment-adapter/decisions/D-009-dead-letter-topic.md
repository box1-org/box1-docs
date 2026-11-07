# D-009 Dead-letter topic for the fulfillment group

**Status:** resolved 2026-11-05 by the user: option A, approved ("do the merges"; D-009 sync approved separately). See evidence/07-release-live.txt.

**Decision:** `box1.fulfillment.dlq.v1`, 3 partitions, replicas 1, 14 days, `cleanup.policy: delete`, as order and inventory. A `TOPICS.md` row in `box1-ops-contracts` (adapter-owned) and a KafkaTopic PR in `box1-gitops` `platform/kafka/topics/`. Merge order: contracts, gitops plus a `box1-kafka` sync of that one resource, then workloads, then the service. The adapter must not be deployed with Kafka consumption before the topic exists: a failed DLQ send crash-loops the pod and broker auto-create would make a one-partition topic.

**Poison:** invalid JSON or envelope, schema-invalid payload, a value ERP1 cannot carry, or a conflicting reuse. Each is also recorded durably in `rejected_command` with the reason.
