# Edge sites 04 — Site status in asset-service and a Sites map in the operations console

> **Service and console work.** The site agent sends a heartbeat to asset-service; asset-service keeps each site's online, degraded or offline state; the operations console Sites page shows them on a map. Read `../00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Merging to a service `main` starts its build and dev promotion: approval needed.
- Detaching a site NIC is a fault injection: approval needed, site VMs only.
- The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not use Chrome.

**Issue:** [box1-docs#130](https://github.com/box1-org/box1-docs/issues/130), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- `01_site_foundation.md`: the site status API in `box1-ops-contracts`.
- `02_site_forwarder_outbox.md`: the buffer-depth metric the heartbeat reports.
- `03_site_machine_identity.md`: the per-site clients and the `siteId` claim check.
- [#138](https://github.com/box1-org/box1-docs/issues/138): the site instances.

## Mission

Each site reports its status to asset-service over HTTPS. asset-service stores the latest status and derives online, degraded or offline from stated thresholds. The operations console Sites page adds a map, each site's state, last-seen time, buffer depth, running image digest and active alerts.

## Verified baseline (observed 2026-11-09; verify before relying)

**asset-service** (main `95bf5c8`)
- No sites table or site endpoints. Staleness is per asset: `asset.stale-after` defaults to PT2M (`AssetConfig.java` L35–37); gauge `asset.assets.stale` reads `asset_last_seen` (`OperationalGauges.java` L43–63).
- Flyway has only `V1`; the next migration is `V2`.
- OIDC (`application.properties` L40–66); unlisted paths are denied (L49–50), so `/api/v1/sites/*` needs a permission set. The `operations-console` client has `telemetry-reader` only (L63).
- Route `asset-service-dev.apps.ocp.box1.org`.

**operations-console** (main `2a4035e7`)
- A Sites page already exists: `webui/src/pages/Sites.tsx` L1–69 ("Sites & assets"), route `/sites` (`main.tsx` L28). It shows active alerts and per-site stock tables.
- React 19, react-router, **react-aria-components (not PatternFly)**, Vite, openapi-fetch.
- The Quarkus backend `ConsoleResource.java` L232–258 serves `GET /api/v1/sites` from inventory stock rows and asset-service alerts. Sites without stock rows do not appear.
- **No map component.** The CSP (`application.properties` L61: `img-src 'self' data:; connect-src 'self'`) blocks external map tiles.

**Booted digest.** The VM golden path's verify checks the approved annotation, not the booted digest (`vm-smoke.yaml` L1–5). `bootc-apply` reads the booted digest over `virtctl ssh`. A guest heartbeat is the third option #138 lists; this prompt provides it.

## Decided design

From the issue and #126's decisions (status lives in asset-service, not a new service).

**Site agent (part of the `gateway` module in `site-gateway`)**
- Periodic heartbeat, `PUT /api/v1/sites/{siteId}/status`, with its client-credentials token from `03`. Body: time, buffer depth and oldest-row age, booted OS image digest (`bootc status --format json`, through a narrowly permitted command as `legacy-erp`'s sudoers precedent does), greenboot status, app versions (bundle digest).
- Failed heartbeats are not buffered for replay; the next one replaces them. Record the interval.

**asset-service**
- `V2` migration: a `site_status` table (latest status per site) and, if useful, a bounded history.
- `PUT /api/v1/sites/{siteId}/status` (site identity, claim checked as `03` decides) and `GET /api/v1/sites`, `GET /api/v1/sites/{siteId}` (readers, including the `operations-console` client), documented in OpenAPI and matching the contract.
- State model: **online / degraded / offline**, from last-seen time and buffer depth, with stated thresholds in configuration. Offline is computed at read time and also exposed as a metric, so `05`'s stale-site alert can use it.
- Metrics per site: last-seen age, buffer depth, state.

**Console**
- The backend adds the asset-service site status call and merges it into `GET /api/v1/sites`, so sites appear even without stock rows.
- The Sites page adds a map: a self-contained SVG with fixed site coordinates in configuration (no external tiles, so the CSP stays as is), plus a table with state, last-seen, buffer depth, image digest and active alerts per site.
- Accessible: state is not shown by colour alone; keyboard operable.

## Scope and guardrails

**In scope:** asset-service endpoints, migration, metrics and tests; the site agent heartbeat in `site-gateway`; the console backend and Sites page; GitOps changes for these services' configuration.

**Out of scope:** reading ingestion and the stale-site PrometheusRule (`05`); Keycloak clients (`03`); greenboot (`08`, which this heartbeat reports).

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #130 only with the evidence named.

- [ ] Both sites show as online in the console, with their last-seen time and the image digest they are actually running.
  - Evidence: a console screenshot or API response, and `bootc status` from each guest showing the same digest.
- [ ] Detaching a site's NIC turns it offline in the console within the stated window, while the other site stays online. Reconnecting returns it to online.
  - Evidence: the approved detach, timestamps of detach, offline and reconnect, and both sites' states over the run.
- [ ] Growing buffer depth is visible, and crossing the threshold marks the site degraded.
  - Evidence: the threshold value, depth over time, and the state change. Kafka paused or a test threshold is acceptable if stated.
- [ ] Anonymous status writes are rejected, and a site cannot write the other site's status.
  - Evidence: `401` anonymous, `403` cross-site, and a successful own-site write.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/130-site-status/`.

**Discovery must cover**
- The merged status API contract and the identity design from `03`.
- How the guest reaches asset-service (Route with public TLS, or the internal Service) and the CA it trusts.
- The console's current Sites page, BFF clients and CSP.
- How the guest can read the booted digest and greenboot status without broad privileges.

**Design decisions to record**
- Heartbeat interval; online, degraded and offline thresholds.
- Storage of status history and its retention.
- Map coordinates and rendering.
- The privilege the agent uses to read `bootc status`.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 2 Contracts | Endpoints match the `box1-ops-contracts` OpenAPI |
| 3 Implementation | Negative security tests; accessibility scan of the Sites page |
| 6 Delivery | asset-service and console promoted by digest; site OS digest carrying the agent on both sites |
| 7 Live acceptance | All four criteria |

**Verification scenarios**
- Heartbeat with a stale timestamp; out-of-order heartbeats; asset-service restart; one site never reporting; a site removed (decommissioned instance) and how it is shown.

**Stop conditions**
- `03` has not delivered the site clients.
- A guest cannot reach asset-service and no route is approved.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the endpoints, thresholds, metric names (used by `05` and `09`), service and site digests, evidence, and rollback (revert the service promotions; the `V2` migration is additive).

Tick the completed items on #130.
