# D-013 Contract changes in box1-ops-contracts

**Status:** decided; PR to be opened under this run's standing permission (schemas and the consumer-group change only). Merge needs approval.

1. `events/v1/notification.delivered.schema.json` — `notificationId` (`^ntf_[A-Za-z0-9_-]+$`), `orderId`, `noticeType` (enum D-002), `channel` (`^ops-[a-z0-9-]+$`), `templateVersion` (`^[A-Z_]+@v[1-9][0-9]*$`), `attemptCount`, `deliveredAt`, `provider` (`stub`), `receiptId` (`^rcpt_[0-9a-f]{24}$`). `additionalProperties: false`.
2. `events/v1/notification.failed.schema.json` — the same identity fields, `attemptCount`, `failedAt`, `provider`, `failureCategory` (`RETRIES_EXHAUSTED` | `PERMANENT_REJECTION`), `failureCode` (fixed enum), `httpStatus` (nullable integer). `additionalProperties: false`. No free-text field.
3. Fixtures for both in `fixtures/events.json`, validated by `npm test`.
4. `TOPICS.md`: add `notification` to the consumer groups of `box1.order.events.v1`.

**Not in that PR:** a `box1.notification.dlq.v1` row in `TOPICS.md`. It belongs with the DLQ approval (D-006) and is outside this run's standing contracts permission. It is prepared on a separate branch and reported as an open decision.

The service validates its produced events and consumed fixtures against the contracts fetched at a pinned commit (`contracts.ref`), as the other services do; no local schema copy.
