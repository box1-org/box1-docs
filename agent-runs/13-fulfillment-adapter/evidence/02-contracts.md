# Phase 2 contracts (2026-11-05 EST)

## ERP1 consumed unchanged
- Pinned `box1-ops-contracts` `eef13ead19aa2ed4b6bae071f26e14dd1676f8f1` (merge of PR #6) in `fulfillment-adapter/pom.xml` `contracts.ref`.
- Tests fetch the spec's fixtures over HTTPS at that commit; nothing is copied. `Erp1FixturesTest`: 65 files, 12 names, 3 equivalence pairs, 3 sequences and 1 mapping, all passing (84 checks). The same 3 sequences pass through the persistent consumer (`ResultIngestionTest`).
- The ERP under test (`box1-ops-erp-simulator` `c84c910`) pins the same commit in its `contracts.lock`.
- No ERP1 change was needed or proposed.

## Adapter-owned contracts
- REST: `src/main/resources/META-INF/openapi.yaml` (OpenAPI 3.1), served at `/q/openapi` and checked by `OpenApiTest`. Not yet proposed to `box1-ops-contracts/openapi/`: that repository hard-codes its validated files in `scripts/validate.mjs`. A PR there is optional and can follow merge of the service PR.
- Dead-letter topic `box1.fulfillment.dlq.v1`: a `TOPICS.md` row is needed (D-009). The PR is prepared after approval of the topic.

## Event compatibility (no event change)
The adapter produces only `shipment.confirmed.v1` and `shipment.failed.v1` on `box1.fulfillment.events.v1`, keyed by `orderId`, with the v1 envelope.

| Consumer | Rule it enforces (discovery) | Adapter behavior | Evidence |
|---|---|---|---|
| order (`8fda087`) | `payload.orderId == aggregateId`; `shipmentId ^shp_[A-Za-z0-9_-]{1,124}$`; `reasonCode ^[A-Z][A-Z0-9_]{0,63}$`; boolean `retryable`; other types dead-lettered | `aggregateId` = `orderId`; ERP shipment IDs are `shp_` + 32 hex; reason codes are the ERP1 uppercase codes; `retryable` is always `false` (D-006); no other types | `ResultIngestionTest` (envelope and payload schemas at `eef13ea`); harness scenarios |
| inventory (`6b722a3`) | confirmed consumes the hold; failed `retryable:false` records reconciliation; other types dead-lettered | one outcome event per request (unique index); redelivery emits nothing new | `ResultIngestionTest.shippedEmitsOneConfirmedEventAndRedeliveryEmitsNoMore`; harness redelivery |
| notification | no repository exists | — | — |

`shippedAt` is the ERP result's `statusAt`; `occurredAt` is the time the adapter applied the result; `causationId` is the `fulfillment.requested.v1` `eventId` (Kafka) or an `api-<uuid>` (REST); `correlationId` and `traceparent` are carried from the request through ERP1.
