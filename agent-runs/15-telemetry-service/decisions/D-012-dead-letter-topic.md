# D-012 Telemetry dead-letter topic

**Status:** OPEN, needs approval (shared infrastructure). The PR is prepared under standing permission; merge and the `box1-kafka` sync are not approved.

- Add `platform/kafka/topics/telemetry-dlq.yaml` in `box1-gitops`: `box1.telemetry.dlq.v1`, 3 partitions, RF 1, `cleanup.policy=delete`, retention 14 days, matching `box1.order.dlq.v1` and `box1.inventory.dlq.v1`. One kustomization line.
- `box1-kafka` has no automated sync. After merge, one selective sync of the new KafkaTopic with prune off (the inventory run's method) creates it. Each is a separate approval.
- Order matters: the topic must be `Ready` before the service release that uses it, or the dead-letter producer fails on the first poison record. The service does not fail startup without it.
