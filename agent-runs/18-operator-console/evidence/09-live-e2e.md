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

# Second run: ERP hold, release and ship (2026-11-06 14:40–14:41 EST)

Order `ord_7ea1520e007d4023a76283efab259a34`: `cust_demo_lin`, `site_nyc` SKU-42 × 1, placed from the dropdowns. The SKU list now showed **99 available**, reflecting the first order's consumed unit. The user operated the ERP console; the run polled the adapter and order-service APIs read-only every 4–5 s.

| Time (EST) | Adapter (fulfillment request) | Order service | Console |
|---|---|---|---|
| 14:40:05 | — | SUBMITTED, then reserved, then FULFILLMENT_REQUESTED (14:40:09) | Awaiting ERP acknowledgement |
| 14:40:12 | PENDING rev 1 | FULFILLMENT_REQUESTED | Accepted by the ERP |
| 14:40:40 | **HELD rev 2** (operator hold) | FULFILLMENT_REQUESTED | **"Held by an ERP operator — Waiting, not a failure. The request continues when the ERP operator releases it."** Neutral waiting style, no failure tone; banner "Awaiting ERP acknowledgement. ERP progress: Held by an ERP operator. Outstanding attempts: 1 upload(s), 0 resend(s)." (`live/e2e-3-held-by-erp-operator.jpg`) |
| ~14:41:15 | PENDING rev 3 (released) | FULFILLMENT_REQUESTED | (polled via API) |
| ~14:41:19 | SHIPPED rev 4, `shp_7a850ee5…` | still FULFILLMENT_REQUESTED for about 4 s | (polled via API) |
| ~14:41:23 | SHIPPED rev 4 | **SHIPPED** | (session ended; see below) |

**Interruption at 14:41:05.** Another run (box1-docs#19, branch `run19-console-scenario-control`) merged box1-workloads-dev#116. It adds the console's `SCENARIO_CONTROLLER_URL` and `CONSOLE_SCENARIO_FORWARD_TOKEN`, and that rolled the console pod (`…dbfdfb6d7-mb7xf`). Because the session key is per pod, the signed-in session ended. The page showed "Your console session has ended — Sign in again" (`live/e2e-4-…jpg`), exactly as designed for a 401. That is live evidence for #79.

The final SHIPPED stage of this order is recorded from the source APIs, not a console screenshot. The first run's console screenshot (`live/e2e-2-shipped.jpg`) already shows the shipped rendering live.

**Observed live across both runs:** Awaiting ERP acknowledgement, Accepted by the ERP, **Held by an ERP operator (not a failure)**, Shipped. Not observed live: queued and uploaded (too fast between refreshes), rejected, needs attention, and "ERP detail unavailable". Those remain proven in CI and locally.

**Note (pointer only):** run 19 added a `scenario-controller` audience and scope mappings to the public `operations-console` client (box1-gitops `32ca46b`, user decision for #19). The controller still requires its own `scenario-viewer`/`scenario-operator` roles (403 otherwise), so a self-obtained console token carries only the scenario rights the person already holds. It remains covered by #79.
