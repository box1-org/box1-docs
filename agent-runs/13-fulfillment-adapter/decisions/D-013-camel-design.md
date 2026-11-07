# D-013 Camel and messaging design

**Status:** decided by the agent in Phase 1, 2026-11-05.

- Named Camel routes: REST DSL routes on Platform HTTP and the Kafka `@Incoming` method both call `direct:accept-command`, the route `fulfillment-accept` (**route 1, acceptance**; corrected after review finding A3); `fulfillment-dispatch` (**2**, scheduler → claim due dispatches → ERP1 `DataFormat` → SFTP upload with temp name and rename); `erp-results` (**3**, SFTP consumer on `outbound/` → framing → section 7 table → commit → move to `consumed/<name>.<nonce>`); `fulfillment-reconcile` (**4**, ack timeouts, resend scheduling, needs-attention); plus `consumed-retention` and `outbound-hidden-sweep` (dot-names the SFTP consumer cannot list).
- Kafka input stays on SmallRye Reactive Messaging, as order and inventory, with the same DLQ and database-outage handling; the `@Incoming` method hands each record to route 1, so there is one acceptance path.
- Outcome events use the inventory outbox pattern (plain `KafkaProducer`, publish after broker acknowledgement, database clock).
- The ERP1 `DataFormat` is the only place legacy records exist; the modern domain never sees `|`, ERP status codes or exchange paths.
- Backend strategy: `FulfillmentBackend` with one implementation `legacy-erp1`; the chosen backend is stored at acceptance.
