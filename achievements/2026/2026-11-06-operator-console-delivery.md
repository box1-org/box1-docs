# Operator console: a React front end on the Java Golden Path, delivered and live

**Date:** 2026-11-05 to 2026-11-06 (America/New_York)

**Status:** Delivered and live in `operations-console-dev`, where an operator can follow a real order from placement through a held ERP request to shipment. [box1-docs#18](https://github.com/box1-org/box1-docs/issues/18) stays open:
- **Ticked with cluster proof:** the live end-to-end, and the Golden Path front-end build.
- **Unticked:** the remaining boxes, each with its proof level stated in issue comments.

This was a `frontier` profile run. Its run state, decisions, evidence (including live screenshots), review findings and pilot log are on branch [`agent-run/18-operator-console`](https://github.com/box1-org/box1-docs/tree/agent-run/18-operator-console/agent-runs/18-operator-console). That branch is not merged.

## Outcome

**box1 Operations** is the operator-facing console at `https://operations-console-dev.apps.ocp.box1.org`. It is one Golden Path Quarkus service with two parts in one pod:
- **A React/TypeScript front end**, built inside the Maven build from a pinned lockfile and served by Quarkus. Nothing loads from a CDN or external font.
- **A console backend.** It holds the Keycloak session, so access and refresh tokens never reach browser JavaScript or storage. It calls order-service, inventory-service, fulfillment-adapter and asset-service on the operator's behalf, and owns no business state.

| Item | Value |
|---|---|
| Repository | [`box1-org/operations-console`](https://github.com/box1-org/operations-console), onboarded by the owner through the Golden Path (template 1.1.0) |
| Run 18's last release | `box1-ci/operations-console-release-ds4rl`: build, security gate (`gate`), promote, shared smoke and `console-smoke` all Succeeded. Source `f202f50`, image `sha256:e81896a82c48564dfb25c3d4805ac4a33b58a9fe51a99b788d248bdb072f22a4`, GitOps [box1-workloads-dev#114](https://github.com/box1-org/box1-workloads-dev/pull/114) → `f334337` |
| Contract | `src/main/resources/META-INF/openapi.yaml` 1.0.0: 10 operations under `/api/v1`, using the BFF's (#17) paths, RFC 9457 Problem JSON with stable codes, and per-source `sources` status |
| Keycloak | Public PKCE client `operations-console`, exact `/callback` and `/signed-out.html` redirects, roles `console-viewer`, `console-operator` and `console-developer` |

**What an operator gets:**
- **Overview.** Business indicators and an exception queue.
- **Orders.** Filter, sort and page over the 200 most recent orders.
- **Place order.** Site and SKU dropdowns from live inventory stock; demo customers or a typed `cust_…` ID; a warning when the quantity exceeds available stock. One idempotency key per submission is kept across retries, so an unconfirmed submit can only replay, never duplicate.
- **Order detail.** State, reservation, **ERP progress** from the adapter, and a timeline whose entries carry trace and correlation IDs. ERP progress reads: queued, uploaded, accepted by the ERP, **held by an ERP operator (waiting, not a failure)**, shipped, rejected, needs attention, or **"ERP detail unavailable"**, never a guessed state.
- **Other pages.** Incidents (derived from order status), Sites & assets, Delivery (each service's deployed revision) and Demo control.
- **Failure handling.** A slow or failed upstream gives a partial page that names it; the page budget is 3 s.

## Starting baseline

- `operations-console` was the Golden Path scaffold: source `5023cda`, image `sha256:00c55736…`, serving `/api/greetings`. No console repository had existed before the owner onboarded it for this issue.
- **The Golden Path build had no Node.** The shared `box1-quarkus-maven` task runs `mvn verify` in a pinned `ubi9/openjdk-21` image. Whether it could build a front end was not established.
- **Upstream access was uneven.**
  - order-service has no authentication (#40).
  - inventory and adapter reads are open in dev.
  - asset-service accepts only tokens issued to its own client.
  - No published API linked an order to its fulfillment request.
- **The ERP could not hold a request on the cluster** at the start: the adapter had SFTP disabled. Another run (#25) connected the ERP appliance VM during this run.
- An HTML/CSS mockup with a capability list existed on branch `issue-18-operator-console-mockup`.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Build probe | [operations-console#1](https://github.com/box1-org/operations-console/pull/1) | closed | Proved the front-end build in the real PR pipeline before any page was written |
| Console | [operations-console#2](https://github.com/box1-org/operations-console/pull/2) | `a8f2140` | Front end, console backend, versioned contract, Firefox e2e suite, docs, `security-gates: gate`, read-only `console-smoke` release step |
| Gate fix | [operations-console#3](https://github.com/box1-org/operations-console/pull/3) | `267152e` | Guava 33.7.2-jre override for CVE-2026-102554 |
| Live spec | [operations-console#4](https://github.com/box1-org/operations-console/pull/4) | `03b4dee` | Read-only acceptance against the real Route; logout must end the SSO session |
| Place order | [operations-console#5](https://github.com/box1-org/operations-console/pull/5) | `f202f50` | Dropdowns from inventory (requested by the owner) |
| Identity | [box1-gitops#73](https://github.com/box1-org/box1-gitops/pull/73) | `09cd71a` | KeycloakClient `operations-console` and console roles |
| Identity | [box1-gitops#77](https://github.com/box1-org/box1-gitops/pull/77) | `c2b5a9b` | Signed-out page as a valid redirect: RH-SSO 7.6 validates the post-logout URI against them |
| Runtime | [box1-workloads-dev#90](https://github.com/box1-org/box1-workloads-dev/pull/90) | `a4e41ea` | Upstream URLs and console settings as Deployment `env`, one replica |
| Runtime | [box1-workloads-dev#115](https://github.com/box1-org/box1-workloads-dev/pull/115) | `9209e09` | `CONSOLE_FULFILLMENT_LINK=derived`, which shows ERP progress (see gap G-1 below) |

The pipeline itself merged the image promotions: #96 → `b3a1a52`, then #114 → `f334337`.

**How the front end builds on the Java Golden Path:**
- Maven downloads Node 24.22.2 from nodejs.org and checks it against a pinned SHA-256 before `frontend-maven-plugin` installs it. The plugin does not verify downloads itself.
- `npm ci` runs from the committed lockfile with install scripts disabled; then `tsc`, then Vite. Quarkus serves the output from `META-INF/resources`.
- The typed client is generated at build time from the same `openapi.yaml` the backend serves. A drift test keeps the two in step.
- The shared build task and smoke task were **not changed**.

**Decisions with consequences** (records are in the run state's `decisions/`):
- **Public client, tokens held server-side, no token forwarding by default.** The client carries only its own audience: the security review showed a public client with other services' audiences would let any realm user mint those tokens. The console reads upstreams without a user token while their reads are open. A confidential client and token strategy is [#79](https://github.com/box1-org/box1-docs/issues/79).
- **Sessions end on every pod restart.** The session key is generated per pod, so there is one replica. This was observed live twice (see validation) and is tracked in #79.
- **The order → fulfillment link is derived (G-1).** The console uses order-service's internal `ful_<id>` naming, labelled "derived link" in the UI. The permanent fix is [#78](https://github.com/box1-org/box1-docs/issues/78).
- **Partial data is reported, never guessed.** A failed source returns null (absent) values, not zeros. Incidents are derived from order status until #17 defines a contract.
- **The customer role is out of scope** (owner's decision). Orders carry no verified customer identity until #40.

## Validation and evidence

| Check | Expected | Observed |
|---|---|---|
| Front end in the Golden Path pipeline | Node build passes, unchanged task | Probe run `operations-console-validate-zqk5s` passed in 1m17s, with the bundle hash identical to the local build; every later PR and release built it. A wrong Node checksum fails the build |
| Maven suite | Pass | 51 unit/HTTP tests + 5 packaged ITs, Checkstyle 0, SpotBugs/FindSecBugs 0. Covers anonymous 401 and no-role 403 on every contract operation, CSRF, partial sources, ERP mapping, and contract drift |
| Firefox e2e (local Keycloak and stubbed upstreams) | Pass | 18/18. Tokens absent from page JS and storage; only the console and Keycloak hosts contacted; logout; roles; order flow through every ERP stage; idempotent retry after a real timeout; axe WCAG 2.1 AA in light and dark with no violations; keyboard-only; 390 px width; no CSP violations |
| Five same-model reviewer passes | Findings fixed or recorded | 43 findings, none High. All in-scope ones fixed and the full suite rerun. Notable: a public client must not carry other audiences; absent values must not show as zero; unconfirmed creates must not duplicate |
| First gated release `-mtdgc` | Gate passes | **Failed**: RHACS policy on CVE-2026-102554 (Guava 33.6.0-jre). Nothing was promoted. Fixed by #3 |
| Releases `-859h8`, `-ds4rl` | All stages pass | Gate (0 critical), promote, smoke and `console-smoke`. The pod's imageID, deployment annotation, `/api/info` gitRef and Argo revision all agree |
| Anonymous API through the Route | 401, no redirect | 401 Problem JSON on all 9 GET paths and the POST |
| Signed-in user with no console role, through the Route | 403 | 403 `ROLE_REQUIRED` on every API path; forbidden page shown |
| Signed-in live checks (Firefox) | Pass | Sign-in via RH-SSO 7.6 with PKCE; tokens absent; only the Route and Keycloak hosts contacted; CSP clean; axe light and dark clean; mobile width; CSRF refusals never reached order-service |
| Logout through the Route | SSO session ends | **First failed:** RH-SSO 7.6 rejected the post-logout URI, so a revisit signed straight back in. Fixed by box1-gitops#77. The live recheck after the fix was **not completed**, because the test account's password had been rotated |
| Live end-to-end, run 1 (2026-11-06 14:28 EST) | Waiting state, recover, shipped | The order was placed from the dropdowns → reserved → **Accepted by the ERP** in 5 s. It waited about 50 s in MANUAL mode, the operator shipped it, then ERP Shipped and order **Shipped**, reservation CONSUMED. One trace ID across the timeline. The console matched the source APIs at every step |
| Live end-to-end, run 2 (14:40 EST) | Hold shown as waiting | The adapter went PENDING rev 1 → **HELD rev 2**. The console showed "Held by an ERP operator — waiting, not a failure". Then PENDING rev 3 (released) → SHIPPED rev 4 → order Shipped |
| One approved pod restart | Observe sessions | The session ended (per-pod key). It also exposed an empty-body 401 (Problem JSON expected), which is fixed in [operations-console#6](https://github.com/box1-org/operations-console/pull/6), not yet merged |

Durable evidence and screenshots are in the run state's `evidence/`, for example `09-live-e2e.md` and `live/e2e-3-held-by-erp-operator.jpg`.

**Not tested or not established:**
- **COMPLETED.** order-service did not advance either order past SHIPPED.
- **The remaining ERP stages live.** Queued and uploaded passed between refreshes; rejected, needs-attention and "ERP detail unavailable" did not occur on the cluster. All three are proven only in CI and locally.
- **Rollback by reverting a promotion commit.** Never exercised.
- **Two replicas.** Not possible with the current session key.

## Final operational state

- **Management:** the console is managed by Argo CD (`operations-console`, auto-sync with self-heal, no prune) from `box1-org/box1-workloads-dev` `workloads/operations-console`. The Keycloak client is managed from `box1-org/box1-gitops` `platform/identity/keycloak/realm/operations-console-client.yaml` (Application `keycloak`).
- **Runtime:** one replica. `CONSOLE_FULFILLMENT_LINK=derived`. No user token is forwarded to inventory or the adapter.
- **Changed by other runs after run 18's last release.** On 2026-11-06 at 20:59 EST the console ran source `e5dc0ec`, image `sha256:c52deca4…` (Argo Synced/Healthy at `3b74650`), after other runs merged:
  - operations-console#7: Demo control drives the scenario controller (#19). It added a `scenario-controller` audience and scope mappings to the console client.
  - #8: OTLP trace export, off by default.
  - #9: asset alerts on Sites (#80).
  - #10: trace links (#22).

  Their records belong to those runs.
- **Credentials:** no secret or credential was added to Git. Test sign-ins used accounts the owner issued for this run.

## Recovery and follow-ups

- **Roll back the console** by reverting the latest promotion commit in `box1-workloads-dev` through a PR. That commit changes both the digest in `kustomization.yaml` and the `box1.org/source-revision` annotation. The console holds no data, and users sign in again. This is **untested**.
- **Hide ERP progress** by setting `CONSOLE_FULFILLMENT_LINK=none` (Deployment env). Pages then show "ERP detail unavailable".
- **Open PR:** [operations-console#6](https://github.com/box1-org/operations-console/pull/6) (favicons resized from the brand mark, the live 403 test, and the empty-401 fix).
- **Backlog:**
  - [#78](https://github.com/box1-org/box1-docs/issues/78): order-service publishes `fulfillmentRequestId` (replaces the derived link).
  - [#79](https://github.com/box1-org/box1-docs/issues/79): confidential client, persistent session key, upstream token strategy.
  - [#80](https://github.com/box1-org/box1-docs/issues/80): asset-service reads from the console.
  - [#81](https://github.com/box1-org/box1-docs/issues/81): Developer Hub API testing with Keycloak-authenticated APIs.
  - [#40](https://github.com/box1-org/box1-docs/issues/40): order-service authentication.
  - [#22](https://github.com/box1-org/box1-docs/issues/22): trace, log and dashboard links.
- **Remaining #18 criteria:**
  - logout recheck after #77;
  - ERP stages not seen live;
  - logo and favicon (#6);
  - error/loading states and keyboard incident traversal proven only locally.

  No owner is assigned.
