# D-011 Logs, traces and metrics

**Status:** decided by the run.

- JSON logs in prod (`quarkus-logging-json`), field `service=notification-service`. MDC: `orderId`, `notificationId`, `eventId`, `eventType`, `correlationId`. No payloads, notice bodies, tokens or provider responses are logged.
- `traceparent` is read from the incoming envelope (as order-service does: envelope, not Kafka headers) and parents a `notification.consume {eventType}` span; the delivery worker starts a `notification.deliver` span linked to the intent's stored traceparent; outbound envelopes carry the delivery span context. Exporters stay `none` until a collector exists (#22).
- Metrics (Micrometer, Prometheus):
  - `box1_notification_events_consumed_total{type,outcome}` (`created`, `merged`, `duplicate`, `ignored`, `skipped_before_floor`, `poison`)
  - `box1_notification_pending` and `box1_notification_oldest_pending_age_seconds`
  - `box1_notification_delivery_attempts_total{outcome}` (`success`, `transient`, `permanent`)
  - `box1_notification_delivered_total`, `box1_notification_failed_total{category}` (`RETRIES_EXHAUSTED` is retry exhaustion)
  - `box1_outbox_pending`, `box1_outbox_oldest_pending_age_seconds`, `box1_outbox_publish_failures_total`
  - `box1_greetings_total` (smoke)
- The operator API returns `correlationId` and `traceparent` per intent, so a notice links to the business order's trace.
