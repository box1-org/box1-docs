# Phase 0 discovery (captured 2026-11-05 18:52–19:20 EST)

Read-only. Sources: three read-only discovery subagents plus direct reads. Secret values were not read.

## Clocks and workstation
- Host and Podman VM clocks agreed at 2026-11-05T23:54:59Z. Podman 6.1.3 rootless, machine `podman-machine-default` 4 CPU / 8 GiB; run15-pg, run15-kafka, run15-keycloak were running (not ours).
- Java 21.0.13, Maven 3.10.0, Node 25.2.1.

## Prompt source
- PR box1-docs#53 MERGED 2026-11-05T23:48:21Z, so the prompt was read from `main` at `fe81297`, not branch `fulfillment-adapter-review`.

## box1-ops-contracts
- `main` = `eef13ead19aa2ed4b6bae071f26e14dd1676f8f1` (merge of PR #6, ERP1). **Pinned for this run.**
- `legacy/erp-file/v1/`: SPEC.md (208 lines), `fixtures/manifest.json` (65 `files`, 3 `equivalence`, 12 `names`, 3 `sequences`, 1 `mapping`), `reference/erp1.mjs`.
- Event schemas: envelope (`additionalProperties:false`), `fulfillment.requested` (single sku/quantity, quantity integer ≥1, no upper bound), `shipment.confirmed`, `shipment.failed` (reasonCode `^[A-Z][A-Z0-9_]*$` ≤64).
- TOPICS.md lists `fulfillment` as a consumer of `box1.order.events.v1`, and `order`, `notification`, `inventory` as consumers of `box1.fulfillment.events.v1`. No fulfillment DLQ row.
- `openapi/` holds order-service.yaml and inventory-service.yaml; `scripts/validate.mjs` hard-codes the files it validates.

## fulfillment-adapter
- `main` = `b23e7dd` (Golden Path scaffold, 2 bot commits). Quarkus platform 3.40.1.1, Java 21; Kafka on, **PostgreSQL off**.
- `quarkus-camel-bom:3.40.1.1` exists: Camel Quarkus 3.40.0 on Camel 4.22.1. SFTP is in `camel-quarkus-ftp` (JSch `com.github.mwiede:jsch` 2.28.6). No `camel-quarkus-sftp`.
- Release pipeline: build → security gates (see #42) → promote → smoke. Smoke asserts the template greeting endpoint, `/api/info` gitRef, health, OpenAPI paths and `box1_greetings_total`.

## box1-workloads-dev (`b8332b7`)
- `workloads/fulfillment-adapter/`: deployment, service, route (edge, `fulfillment-adapter-dev.apps.ocp.box1.org`), namespace, serviceaccount, onboarding; **`postgres.yaml` is 0 bytes and not in the kustomization.** ConfigMap generator literals: greeting, JAVA_TOOL_OPTIONS, KAFKA_BOOTSTRAP_SERVERS. Resources 100m/256Mi requests, 1 CPU/512Mi limits.
- order and inventory carry the template database pattern behind box1-docs#41 (details withheld; see #41).

## box1-gitops (`b8054eb`)
- Kafka `box1-kafka` 4.2.0, Streams operator 3.2.2; topics `box1.order.events.v1` (7d), `box1.fulfillment.events.v1` (14d), `box1.order.dlq.v1`, `box1.inventory.dlq.v1`; **no fulfillment DLQ**. Argo `box1-kafka` sync is manual.
- Keycloak: RH-SSO 7.6 (`keycloak.org/v1alpha1`), realm `box1`, clients `openshell-cli`, `developer-hub`. No client for order, inventory or the adapter.
- Kafka security posture: reported to the user directly; not recorded here.

## Cluster (read-only)
- OpenShift 5.0.0-rc.7, single node. CPU requests 74 %, memory requests 68 % of allocatable.
- `fulfillment-adapter-dev`: one scaffold pod at `sha256:beb87256…`, Argo `fulfillment-adapter` Synced/Healthy at `b8332b7`. No PVC and no app Secret.
- No ExternalSecrets, SealedSecrets or Vault CRDs. No ERP VM and no SFTP Service in any namespace.

## Producer and consumers
- order-service `8fda087` produces `fulfillment.requested.v1` on `box1.order.events.v1`, key orderId, from a transactional outbox; `fulfillmentRequestId = "ful_" + orderId suffix`. It consumes `shipment.*`: `retryable:false` → EXCEPTION, `retryable:true` → note; payload `orderId` must equal envelope `aggregateId`; any other event type on the fulfillment topic is dead-lettered.
- inventory-service `6b722a3`: confirmed consumes the hold; failed `retryable:false` records reconciliation; `retryable:true` ignored; other types dead-lettered.
- No notification service repository exists.
- Evidence suggests no `fulfillment.requested.v1` has been produced on the cluster (two live orders are `SUBMITTED`; inventory reserved 0). Not proven without reading the topic.

## ERP (#14) and VM (#25)
- #14 run state: `origin/agent-run/14-erp-appliance` at `e48e036`; decisions D-003..D-007, D-009, D-011, D-013 bind the adapter (summarised in decisions/D-000-inherited-erp1.md).
- ERP code is local only (`run14-erp` at `f15513c`, no remote). `box1-org/box1-ops-erp-simulator` exists but is empty.
- The local ERP `contracts.lock` pins `b20694c`, before `UNREADABLE` was added (for #14 to repin; not changed here).
- #14 and #25 are open with no boxes ticked. No VM or SFTP endpoint exists.
