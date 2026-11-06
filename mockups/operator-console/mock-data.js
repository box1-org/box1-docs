// SYNTHETIC mockup fixtures. No real customers, credentials or endpoints.
// Anchors: run15-contracts/fixtures/events.json (ord_1042, cust_demo_1, corr-1042),
// inventory-service V2__seed_lab_fixture.sql (sites/SKUs), asset-service (asset_press_7).
// Anything not backed by a contract is listed in MOCK.assumptions.
window.MOCK = (() => {
  const T = (hhmm, ss = "00") => `2026-11-05T${hhmm}:${ss}-05:00`;
  const trace = (n) => `4bf92f3577b34da6a3ce929d0e0e${String(4700 + n).padStart(4, "0")}`;

  const stateLabels = {
    SUBMITTED: "Submitted",
    RESERVED: "Stock reserved",
    FULFILLMENT_REQUESTED: "Awaiting ERP acknowledgement",
    SHIPPED: "Shipped",
    COMPLETED: "Completed",
    REJECTED: "Rejected",
    EXCEPTION: "Exception — manual reconciliation",
    CANCELLED: "Cancelled",
  };
  const happyPath = ["SUBMITTED", "RESERVED", "FULFILLMENT_REQUESTED", "SHIPPED", "COMPLETED"];

  const customers = [
    { id: "cust_demo_1", name: "Demo Customer One (synthetic)" },
    { id: "cust_demo_2", name: "Demo Customer Two (synthetic)" },
    { id: "cust_demo_3", name: "Demo Customer Three (synthetic)" },
  ];

  const sites = [
    { siteId: "site_nyc", name: "NYC fulfilment site", status: "ACTIVE", stock: { "SKU-42": 100, "SKU-7": 25, "SKU-LAST": 1 } },
    { siteId: "site_bos", name: "BOS fulfilment site", status: "ACTIVE", stock: { "SKU-42": 10 } },
    { siteId: "site_closed", name: "Closed site", status: "UNAVAILABLE", stock: { "SKU-42": 50 } },
  ];

  const assets = [
    { assetId: "asset_press_7", siteId: "site_nyc", kind: "Packaging press", lastReading: { metric: "temperature_c", value: 81.4, at: T("10:41") },
      alerts: [{ alertId: "alt_0031", status: "ACTIVE", severity: "WARNING", threshold: 80, peak: 83.2, last: 81.4, openedAt: T("10:22") }] },
    { assetId: "asset_conveyor_2", siteId: "site_nyc", kind: "Conveyor", lastReading: { metric: "vibration_mm_s", value: 2.1, at: T("10:41") }, alerts: [] },
    { assetId: "asset_scanner_1", siteId: "site_bos", kind: "Label scanner", lastReading: null, alerts: [] },
  ];

  // Timeline entries mirror order-service.yaml TimelineEntry.
  const tl = (seq, kind, fromState, toState, at, eventType, n, extra = {}) =>
    ({ sequence: seq, kind, fromState, toState, occurredAt: at, eventType, eventId: `evt_${n}_${seq}`, traceId: trace(n), ...extra });

  const orders = [
    { orderId: "ord_1042", state: "COMPLETED", customerId: "cust_demo_1", sku: "SKU-42", quantity: 2, siteId: "site_nyc",
      reservationId: "res_1042", fulfillmentId: "ful_1042", correlationId: "corr-1042", createdAt: T("09:02"), updatedAt: T("09:06"),
      fulfillmentAttempts: [{ attempt: 1, at: T("09:03", "05"), result: "ACKNOWLEDGED" }], notification: { channel: "email", outcome: "SENT", at: T("09:06", "02") },
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("09:02"), "order.submitted.v1", 42),
        tl(2, "TRANSITION", "SUBMITTED", "RESERVED", T("09:02", "03"), "inventory.reserved.v1", 42),
        tl(3, "TRANSITION", "RESERVED", "FULFILLMENT_REQUESTED", T("09:02", "03"), "fulfillment.requested.v1", 42),
        tl(4, "TRANSITION", "FULFILLMENT_REQUESTED", "SHIPPED", T("09:05", "40"), "shipment.confirmed.v1", 42),
        tl(5, "TRANSITION", "SHIPPED", "COMPLETED", T("09:05", "40"), "order.completed.v1", 42),
      ] },
    { orderId: "ord_1043", state: "FULFILLMENT_REQUESTED", stuck: true, customerId: "cust_demo_2", sku: "SKU-7", quantity: 1, siteId: "site_nyc",
      reservationId: "res_1043", fulfillmentId: "ful_1043", correlationId: "corr-1043", createdAt: T("10:14"), updatedAt: T("10:39"), incidentId: "inc_0007",
      fulfillmentAttempts: [
        { attempt: 1, at: T("10:14", "06"), result: "TIMEOUT" },
        { attempt: 2, at: T("10:19", "06"), result: "TIMEOUT" },
        { attempt: 3, at: T("10:29", "06"), result: "PENDING" },
      ], notification: { channel: "email", outcome: "NOT_SENT", at: null },
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("10:14"), "order.submitted.v1", 43),
        tl(2, "TRANSITION", "SUBMITTED", "RESERVED", T("10:14", "04"), "inventory.reserved.v1", 43),
        tl(3, "TRANSITION", "RESERVED", "FULFILLMENT_REQUESTED", T("10:14", "04"), "fulfillment.requested.v1", 43),
        tl(4, "NOTE", null, null, T("10:19", "06"), "shipment.failed.v1", 43, { reasonCode: "ERP_TIMEOUT", note: "Retryable ERP timeout — attempt 1 of 5" }),
        tl(5, "NOTE", null, null, T("10:29", "06"), "shipment.failed.v1", 43, { reasonCode: "ERP_TIMEOUT", note: "Retryable ERP timeout — attempt 2 of 5" }),
      ] },
    { orderId: "ord_1044", state: "EXCEPTION", statusReason: "RESERVATION_EXPIRED", customerId: "cust_demo_3", sku: "SKU-LAST", quantity: 1, siteId: "site_nyc",
      reservationId: "res_1044", correlationId: "corr-1044", createdAt: T("08:40"), updatedAt: T("09:10"),
      fulfillmentAttempts: [{ attempt: 1, at: T("08:40", "05"), result: "TIMEOUT" }], notification: { channel: "email", outcome: "NOT_SENT", at: null },
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("08:40"), "order.submitted.v1", 44),
        tl(2, "TRANSITION", "SUBMITTED", "RESERVED", T("08:40", "02"), "inventory.reserved.v1", 44),
        tl(3, "TRANSITION", "RESERVED", "FULFILLMENT_REQUESTED", T("08:40", "02"), "fulfillment.requested.v1", 44),
        tl(4, "TRANSITION", "FULFILLMENT_REQUESTED", "EXCEPTION", T("09:10"), "inventory.reservation-expired.v1", 44, { reasonCode: "RESERVATION_EXPIRED" }),
      ] },
    { orderId: "ord_1045", state: "SUBMITTED", customerId: "cust_demo_1", sku: "SKU-42", quantity: 5, siteId: "site_bos", correlationId: "corr-1045",
      createdAt: T("10:40"), updatedAt: T("10:40"), fulfillmentAttempts: [], notification: null,
      timeline: [tl(1, "TRANSITION", null, "SUBMITTED", T("10:40"), "order.submitted.v1", 45)] },
    { orderId: "ord_1046", state: "SHIPPED", customerId: "cust_demo_2", sku: "SKU-42", quantity: 3, siteId: "site_bos", reservationId: "res_1046", correlationId: "corr-1046",
      createdAt: T("09:30"), updatedAt: T("09:41"), fulfillmentAttempts: [{ attempt: 1, at: T("09:30", "04"), result: "ACKNOWLEDGED" }], notification: { channel: "email", outcome: "SENT", at: T("09:41") },
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("09:30"), "order.submitted.v1", 46),
        tl(2, "TRANSITION", "SUBMITTED", "RESERVED", T("09:30", "02"), "inventory.reserved.v1", 46),
        tl(3, "TRANSITION", "RESERVED", "FULFILLMENT_REQUESTED", T("09:30", "02"), "fulfillment.requested.v1", 46),
        tl(4, "TRANSITION", "FULFILLMENT_REQUESTED", "SHIPPED", T("09:41"), "shipment.confirmed.v1", 46),
      ] },
    { orderId: "ord_1047", state: "REJECTED", statusReason: "SITE_UNAVAILABLE", customerId: "cust_demo_3", sku: "SKU-42", quantity: 2, siteId: "site_closed", correlationId: "corr-1047",
      createdAt: T("09:50"), updatedAt: T("09:50", "02"), fulfillmentAttempts: [], notification: { channel: "email", outcome: "SENT", at: T("09:50", "05") },
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("09:50"), "order.submitted.v1", 47),
        tl(2, "TRANSITION", "SUBMITTED", "REJECTED", T("09:50", "02"), "inventory.rejected.v1", 47, { reasonCode: "SITE_UNAVAILABLE" }),
      ] },
    { orderId: "ord_1048", state: "FULFILLMENT_REQUESTED", stuck: true, customerId: "cust_demo_1", sku: "SKU-42", quantity: 1, siteId: "site_nyc",
      reservationId: "res_1048", correlationId: "corr-1048", createdAt: T("10:21"), updatedAt: T("10:31"), incidentId: "inc_0007",
      fulfillmentAttempts: [{ attempt: 1, at: T("10:21", "04"), result: "TIMEOUT" }, { attempt: 2, at: T("10:31", "04"), result: "PENDING" }], notification: null,
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("10:21"), "order.submitted.v1", 48),
        tl(2, "TRANSITION", "SUBMITTED", "RESERVED", T("10:21", "03"), "inventory.reserved.v1", 48),
        tl(3, "TRANSITION", "RESERVED", "FULFILLMENT_REQUESTED", T("10:21", "03"), "fulfillment.requested.v1", 48),
        tl(4, "NOTE", null, null, T("10:31", "04"), "shipment.failed.v1", 48, { reasonCode: "ERP_TIMEOUT", note: "Retryable ERP timeout — attempt 1 of 5" }),
      ] },
    { orderId: "ord_1049", state: "CANCELLED", customerId: "cust_demo_2", sku: "SKU-7", quantity: 4, siteId: "site_bos", correlationId: "corr-1049",
      createdAt: T("08:15"), updatedAt: T("08:20"), fulfillmentAttempts: [], notification: null,
      timeline: [
        tl(1, "TRANSITION", null, "SUBMITTED", T("08:15"), "order.submitted.v1", 49),
        tl(2, "TRANSITION", "SUBMITTED", "CANCELLED", T("08:20"), "order.cancelled.v1", 49),
      ] },
  ];

  // ASSUMED: no incident schema exists in any contract (see CAPABILITIES.md gaps).
  const incidents = [
    { incidentId: "inc_0007", title: "ERP acknowledgement latency above SLO", status: "OPEN", severity: "CRITICAL",
      openedAt: T("10:24"), scenarioRunId: "scn_run_0012 (erp-slowdown)", linkedOrders: ["ord_1043", "ord_1048"],
      slo: { name: "Order fulfilment acknowledgement p95 < 120 s", observed: "p95 = 412 s over 15 min" },
      recovery: { requested: false, requestedBy: null, confirmedByBackend: false },
      evidence: [
        { source: "Traces", sourceStatus: "OK", summary: "fulfillment-adapter → erp-sim span p95 410 s; 0 errors, timeouts only", link: "trace:4bf92f3577b34da6a3ce929d0e0e4743" },
        { source: "Logs", sourceStatus: "OK", summary: "WARN erp-sim: ack queue depth 37 (corr-1043, corr-1048)", link: "logs:corr-1043" },
        { source: "Metrics", sourceStatus: "PARTIAL", summary: "erp_ack_latency available; broker lag series missing for last 6 min", link: "dashboard:orders-slo" },
        { source: "Recent changes", sourceStatus: "UNAVAILABLE", summary: "Change feed did not respond (Problem: 504 upstream timeout). Change correlation is unknown, not absent.", link: null },
      ] },
    { incidentId: "inc_0006", title: "Packaging press temperature warning", status: "MONITORING", severity: "WARNING",
      openedAt: T("10:22"), linkedOrders: [], slo: null, recovery: { requested: false, confirmedByBackend: false },
      evidence: [{ source: "Asset telemetry", sourceStatus: "OK", summary: "asset_press_7 temperature 81.4 °C (threshold 80)", link: "alert:alt_0031" }] },
  ];

  // From 09_scenario_controller.md catalog.
  const scenarios = [
    { name: "baseline-order", effect: "Seeds one order and follows the happy path", ttl: "5 min" },
    { name: "inventory-contention", effect: "Two orders compete for SKU-LAST; exactly one reservation", ttl: "5 min" },
    { name: "broker-outage", effect: "Pauses event delivery; outbox backlog grows", ttl: "10 min" },
    { name: "erp-slowdown", effect: "ERP sim delays acknowledgements; SLO alert fires", ttl: "15 min", running: { runId: "scn_run_0012", by: "demo.admin", at: T("10:13") } },
    { name: "ambiguous-erp-timeout", effect: "ERP applies the shipment but the ack is lost", ttl: "10 min" },
    { name: "poison-event", effect: "Publishes an event for an unknown order", ttl: "5 min" },
    { name: "bad-artifact-gate", effect: "Submits an image that fails the delivery gate", ttl: "10 min" },
  ];
  const scenarioAudit = [
    { runId: "scn_run_0012", scenario: "erp-slowdown", action: "start", actor: "demo.admin", at: T("10:13"), env: "box1-demo / orders-demo", result: "RUNNING" },
    { runId: "scn_run_0011", scenario: "baseline-order", action: "reset", actor: "demo.admin", at: T("09:01"), env: "box1-demo / orders-demo", result: "VERIFIED" },
  ];

  // ASSUMED: BFF delivery endpoint does not exist yet. Digests are placeholders, not real images.
  const delivery = [
    { service: "order-service", revision: "a1b2c3d (mock)", digest: "sha256:0000…mock01", sync: "Synced", health: "Healthy", at: T("08:55") },
    { service: "inventory-service", revision: "d4e5f6a (mock)", digest: "sha256:0000…mock02", sync: "Synced", health: "Healthy", at: T("08:50") },
    { service: "fulfillment-adapter", revision: "b7c8d9e (mock)", digest: "sha256:0000…mock03", sync: "OutOfSync", health: "Healthy", at: T("10:02") },
    { service: "box1-ops-bff", revision: "—", digest: "—", sync: "Unknown", health: "Not deployed", at: null },
  ];

  const roles = {
    customer:  { label: "Customer", routes: ["orders", "order", "new"] },
    operator:  { label: "Operator", routes: ["home", "orders", "order", "new", "incidents", "incident", "sites", "demo"] },
    developer: { label: "Developer", routes: ["home", "orders", "order", "incidents", "incident", "sites", "delivery"] },
    admin:     { label: "Admin", routes: ["home", "orders", "order", "new", "incidents", "incident", "sites", "demo", "delivery"] },
  };

  const assumptions = [
    "Incident/evidence shape (no contract exists)",
    "BFF /overview and /orders/{id}/summary field names (prose only in 07_experience_bff.md)",
    "Delivery panel data source (no endpoint defined)",
    "Role → page matrix (FR-08 is undefined)",
    "Customer display names, assets other than asset_press_7, orders other than ord_1042",
  ];

  return { stateLabels, happyPath, customers, sites, assets, orders, incidents, scenarios, scenarioAudit, delivery, roles, assumptions,
    env: { cluster: "box1-demo", namespace: "orders-demo" }, now: T("10:42") };
})();
