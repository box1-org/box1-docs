# Kafka and PostgreSQL foundation runbook

Validated evidence baseline: **2026-11-01, America/New_York**. This runbook records the Box1 Platform 01 foundation state and the procedures for completing the remaining live acceptance checks. It does not claim production HA or vendor support for the single-node OpenShift lab.

## Final observed state

- GitOps `main` revision: [`e3c33a1`](https://github.com/box1-org/box1-gitops/commit/e3c33a1729dd85fa4bfd661c5e59d83799533ce5), including the merged shared-topic change.
- Shared contracts repository: [`box1-org/box1-ops-contracts`](https://github.com/box1-org/box1-ops-contracts).
- Kafka Argo Application: `box1-kafka`, `Synced/Healthy`, revision `e3c33a1`.
- Kafka: `Ready=True`, Strimzi API `v1`, Kafka `4.2.0`, metadata version `4.2`, KRaft mode, one broker/controller, 10Gi `lvms-vg1` PVC.
- Kafka broker and Entity Operator pods: `Running` and ready.
- Shared topics: all five are `Ready=True` with replication factor one:
  - `box1.order.events.v1` — 3 partitions, 7-day retention
  - `box1.inventory.events.v1` — 3 partitions, 7-day retention
  - `box1.fulfillment.events.v1` — 3 partitions, 14-day retention
  - `box1.telemetry.events.v1` — 6 partitions, 2-day retention
  - `box1.notification.events.v1` — 3 partitions, 14-day retention
- Kafka authentication incident: the operator reported PKIX signature failures while the broker retained stale certificate/DNS state. The AMQ Streams operator was restarted, then the single broker pod was restarted to reload generated certificate material. Kafka subsequently became Ready. These restarts were recovery actions, not persistent Git changes.
- PostgreSQL guidance and migration fixtures are in [`box1-ops-contracts#1`](https://github.com/box1-org/box1-ops-contracts/pull/1). No live service database isolation or restore drill has been established.

## Kafka operations

Inspect readiness and topics:

```sh
oc get kafka box1-kafka -n box1-kafka
oc get kafkatopic -n box1-kafka
oc get pods -n box1-kafka -o wide
```

The broker bootstrap address for in-cluster clients is:

```text
box1-kafka-kafka-bootstrap.box1-kafka.svc:9092
```

Order lifecycle events use `orderId` as the partition key. Telemetry uses `assetId`; notification and fulfillment events retain order correlation. Consumer groups and retention ownership are defined in [`TOPICS.md`](https://github.com/box1-org/box1-ops-contracts/blob/main/TOPICS.md). The current manifests establish topics and retention only; DLQ topics, retry policy, replay authorization, and audit records still require application implementation and live verification.

For a broker authentication failure:

1. Capture the Kafka and operator conditions and recent logs before restarting anything.
2. Verify the broker certificate chains to `box1-kafka-cluster-ca-cert` and compare the broker pod start time with the generated certificate Secret timestamp.
3. Restart the AMQ Streams operator deployment if its AdminClient has stale certificate/DNS state.
4. Restart the single broker pod if it started before the current generated certificate Secret. Confirm the broker returns `Ready` before creating topics or running clients.
5. Do not delete cluster CA Secrets, broker PVCs, or Kafka data as an authentication workaround.

## PostgreSQL bootstrap and ownership

Use one database and login per service. The runtime login must not read or write another service’s database/schema. Store the Secret outside Git; the generated service template’s `replace-before-sync` value is a blocking placeholder, not a usable credential.

The ownership matrix, Secret keys, Flyway rules, storage profile, backup, and restore commands are maintained in:

- [`postgres/OWNERSHIP.md`](https://github.com/box1-org/box1-ops-contracts/blob/main/postgres/OWNERSHIP.md)
- [`postgres/MIGRATIONS.md`](https://github.com/box1-org/box1-ops-contracts/blob/main/postgres/MIGRATIONS.md)
- [`postgres/SECRETS.md`](https://github.com/box1-org/box1-ops-contracts/blob/main/postgres/SECRETS.md)
- [`postgres/STORAGE-BACKUP-RESTORE.md`](https://github.com/box1-org/box1-ops-contracts/blob/main/postgres/STORAGE-BACKUP-RESTORE.md)

The lab storage profile is `lvms-vg1`, `ReadWriteOnce`, with 5Gi as the generated starting request. This is node-local single-node storage and does not establish HA.

## Acceptance drills and evidence

The local harness in [`box1-ops-contracts#2`](https://github.com/box1-org/box1-ops-contracts/pull/2) passes:

```sh
npm test
npm run test:drills
npm run validate
```

Those tests establish deterministic simulation behavior for outbox replay, redelivery/DLQ, owner isolation, and checksum restore. They do not establish live PostgreSQL or Kafka behavior.

Remaining live checks:

- Create isolated order and inventory databases/users; prove each cross-service read/write is denied.
- Commit an order and outbox row, stop the publisher before publish, restart it, and verify one logical event is emitted.
- Force a consumer failure, observe bounded redelivery and DLQ placement, then perform an authorized replay with an audit record.
- Run `pg_dump` from a seeded database, restore into a disposable database, and compare the documented checksum/row set.
- Add and verify service-namespace topic provisioning only after reviewing the required Argo/Topic Operator permission boundary. The current shared Entity Operators are intentionally scoped to `box1-kafka`.

## Rollback and recovery

- Kafka manifest rollback: revert the reviewed GitOps commit that changed the Kafka CR, node pool, or topic manifests, then sync `box1-kafka`. Preserve the Kafka PVC and cluster CA Secrets unless a separately approved data-disaster procedure requires otherwise.
- Topic rollback: stop producers and consumers, preserve topic data for the retention window, and remove a topic manifest only through a reviewed GitOps change. Topic deletion is not a routine rollback and is not tested here.
- PostgreSQL migration rollback: use a forward-compatible corrective migration. Do not edit or delete an applied Flyway migration. For data recovery, restore into an isolated database first and record checksum evidence before any cutover.
- Credential recovery: rotate the database role and update the approved Secret reference; restart or reload the service, then perform a connection check. Do not print credentials or commit them.

## Limitations and backlog state

Issue [#21](https://github.com/box1-org/box1-docs/issues/21) remains open because live DB isolation, Kafka redelivery/DLQ replay, outbox crash recovery, and PostgreSQL restore have not been exercised. The generated-service KafkaTopic fix remains [box1-templates#5](https://github.com/box1-org/box1-templates/pull/5), and service-namespace topic permissions require a separate security review. Do not close the issue until those acceptance checks have durable observed evidence.
