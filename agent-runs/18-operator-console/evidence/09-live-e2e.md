# Live end-to-end through the real ERP (2026-11-06, America/New_York)

- **Driver:** the console on the real Route (`operations-console-dev.apps.ocp.box1.org`), image `sha256:e81896a8…` (source `f202f50`), `CONSOLE_FULFILLMENT_LINK=derived` (box1-workloads-dev#115, pod Ready 14:24 EST).
- **Browser:** the Claude desktop app's built-in browser pane. The user signed in themself; the session belongs to **mike** (console-viewer, -operator, -developer).
- **ERP:** the legacy ERP appliance VM, reached by the adapter over SFTP (`legacy-erp-sftp.legacy-erp-dev.svc`). The user put the ERP in **MANUAL** mode and operated its console. The run never touched the ERP.

## Timeline (all observed in the console and confirmed against the source APIs)

| Time (EST) | Observed in the console | Source |
|---|---|---|
| 14:28:4x | Place order: dropdowns listed live inventory sites (`site_bos`, `site_closed`, `site_nyc`); `site_nyc` SKU-42 "100 available (100 on hand, 0 reserved)"; `cust_demo_ada`, quantity 1 | `/api/v1/sites` |
| 14:28:43 | "Order accepted by the order service", `ord_8500479e37b34b84b593290e71bea1a0`, Submitted | order-service |
| 14:28:45 | Submitted → Stock reserved → **Awaiting ERP acknowledgement**; reservation `res_c10faa40…` COMMITTED | order-service, inventory |
| 14:28:48 | ERP panel **"Accepted by the ERP"**: dispatch UPLOADED, ACKNOWLEDGED, outcome PENDING rev 1, 1 upload / 0 resends, request `ful_8500479e…` (derived link). Banner: "Awaiting ERP acknowledgement. ERP progress: Accepted by the ERP. Outstanding attempts: 1 upload(s), 0 resend(s)." The order **waited about 50 s for the ERP operator** (MANUAL mode) | fulfillment-adapter |
| 14:29:39 | ERP outcome **SHIPPED rev 2**, shipment `shp_05fdfdab…` | fulfillment-adapter |
| 14:29:42 | Order **Shipped** (`shipment.confirmed.v1`); reservation CONSUMED | order-service, inventory |
| 14:30:55 | Order still SHIPPED; order-service has not moved it to COMPLETED. The console keeps refreshing and claims no completion | order-service |

- **Diagnosis links:** every timeline entry carries trace `f50e6a91d334d1648a3e2c6f71d445e2` and correlation `e4e14d6c-…` with event IDs. The evidence section links the order-service revision `11360f2a56a6`. Trace, log and dashboard links say "not available until box1-docs#22".
- **Screenshots:** `live/e2e-1-accepted-by-erp.jpg`, `live/e2e-2-shipped.jpg`.

## What this proves and what it does not
- **Proven on the cluster:** seed → submit → watch the timeline → ERP processing delayed (MANUAL; waiting state with diagnosis links) → recover (operator ships) → visibly shipped. The console's ERP stages matched the adapter's fields exactly at every observation.
- **Not exercised:** an ERP **hold**. The adapter's revisions go PENDING (1) → SHIPPED (2), with no HELD revision. "Held by an ERP operator" is therefore still proven only locally.
- **Not reached:** **COMPLETED**. order-service did not advance SHIPPED → COMPLETED ("if the completion policy allows", ORDER-STATE.md).
- **Not observed live:** queued and uploaded-awaiting-ack. They passed within 5 s, between console refreshes.
