# D-006 Consumers, first-start offset policy, poison handling and dead-letter topic

**Status:** offset policy decided by the run. **The dead-letter topic needs user approval** (shared infrastructure).

## Channels

Two SmallRye Kafka channels, group `notification`, as in order-service: `order-events` on `box1.order.events.v1` and `fulfillment-events` on `box1.fulfillment.events.v1`. Byte-array values, String keys, `@Blocking`, offsets committed after processing. `throttled.unprocessed-record-max-age.ms=-1`, as in order-service, so a held record does not restart the pod.

## First-start offset policy

`auto.offset.reset=earliest` **plus a required floor** `NOTIFY_EVENTS_FLOOR` (ISO-8601 instant, no default), the pattern inventory-service chose (#12 D-002):

- Startup fails if the floor is missing, unparsable or in the future.
- An event whose envelope `occurredAt` is before the floor is acknowledged with no intent and no dedupe row, and counted as `skipped_before_floor`.
- The floor is set in the Deployment `env`, to the time of the deployment PR. **A new consumer group therefore does not replay a week of order history (or two weeks of fulfillment history) into notices.** Replaying history on purpose is a reviewed change of the floor.
- `earliest` (not `latest`) so that events published between the floor and the first partition assignment are not lost, and so an offset reset after `offsets.retention` expiry is still bounded by the floor.

## Poison and transient errors

Poison goes unchanged to the dead-letter topic through the connector's `dead-letter-queue` failure strategy:

- the value is not UTF-8 JSON, or the envelope fails the v1 envelope rules;
- `eventType` is not one of the types the topic's contract lists;
- a payload this service consumes fails its schema rules, or `aggregateId` differs from `payload.orderId`.

Exception messages are fixed text naming the rule, never field values (they reach DLQ headers).

Unknown orders are not poison here: this service does not know orders and must not read order-service tables. The `ORDER-STATE.md` unknown-order rule applies to the order owner.

Transient database errors: when the database cannot serve (SQLState classes 08, 53, 57P or none), the record is held and retried every 30 s at most without using attempts; other transient errors get 20 attempts capped at 30 s, then the record goes to the DLQ, as in inventory-service.

## Dead-letter topic (approval required)

`box1.notification.dlq.v1`, 3 partitions, RF 1, 14 d, `cleanup.policy: delete`, identical to the existing DLQ topics. It must exist before the service consumes on the cluster: a failed DLQ send stops the channel, and broker auto-create would create a 1-partition topic. Delivered as a box1-gitops KafkaTopic PR, then a selective `box1-kafka` sync of that resource with prune off. Each is a separate approval.

**Privacy caveat:** a poisoned `order.placed.v1` record (the only event with `customerId`) would be copied unchanged to the DLQ, keeping data already on the order topic for 14 d instead of 7 d. A well-formed `order.placed.v1` is never poison here, because only its envelope is read.

## Replay

Operator procedure in `docs/runbook.md`: inspect with `kafka-console-consumer.sh --property print.headers=true`, fix the cause, re-produce the unchanged key and value to the source topic, recording who and why. The consumer is duplicate-safe (D-003). No HTTP replay endpoint.
