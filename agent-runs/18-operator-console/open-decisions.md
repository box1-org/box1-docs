# Open decisions and gaps for the user

Each item says what is blocked and what proceeds without it. Updated 2026-11-05 ~23:05 EST.

| # | Decision | Blocks | Proceeding meanwhile | Recommendation |
|---|---|---|---|---|
| O-1 | **Order → fulfillment link (G-1).** No published API links an order to its fulfillment. Either (a) use order-service's internal `ful_<id>` convention, labelled "derived link", until (b) order-service exposes `fulfillmentRequestId` (a change to another service and its contract, out of scope). | Live ERP refinement on order detail (CON-ERP-001 live) | Mapping built and tested against stubs, behind the `CONSOLE_FULFILLMENT_LINK` switch, which defaults to `none` | (a) as an interim, plus a backlog issue for (b) |
| O-2 | **asset-service refuses console tokens (G-2).** It requires `azp=asset-service`. Options: (a) asset-service also accepts `azp=operations-console` for reads, which is a change to asset-service; (b) the console shows telemetry as `NOT_AUTHORIZED` and links to the asset console. | Telemetry alerts on Sites and Incidents | (b) is implemented | (b) now; (a) as a backlog item if wanted |
| O-3 | **Session encryption key (new secret).** Without it, every restart signs users out and the console stays at one replica (as #63). | Restart-survival only | One replica; the limit is recorded and observed | Approve together with #63's approach, or accept the limit |
| O-4 | **Favicon by resizing the brand mark** (32×32, 180×180, resize only). Also confirm the mark is the brand-kit asset. | CON-BRAND-001 completion | The unmodified PNG is used as the icon | Approve |
| O-5 | **Customer role out of scope.** No verified customer identity exists (#40). | CON-CUST-001 (recorded `blocked`) | Staff roles only | Confirm |
| O-6 | **Seed fixtures on the cluster:** customers `cust_demo_ada/lin/kai`, keys `demo-<scenario>-<date>-<n>`. Additive only; nothing is deleted. | Phase 7 E2E and screenshots | Local stubs | Approve the named set when Phase 7 starts |
| O-7 | **Keycloak client `operations-console`** (box1-gitops PR, D-002): merge, then **assign roles to your user(s)**. | Real sign-in (Phase 7) | Local Keycloak | Approve when the PR is open |
| O-8 | **No ERP can hold a request on the cluster (G-3).** The deployed adapter has `FULFILLMENT_SFTP_ENABLED=false`, and the ERP VM has no Service. Enabling it is a fulfillment-adapter/#25 change. | AC1 live E2E with a held request | Held state proven locally against stubs | Leave the AC1 box unticked until #25 wires the adapter to the VM |
| — | Every merge (operations-console, box1-workloads-dev promotion, box1-gitops) | Delivery | — | One approval per merge |
