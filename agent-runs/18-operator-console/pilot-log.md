# Frontier profile pilot log: box1-docs#18

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|
| 2 | 2026-11-06 ~00:27 EST | 7 | Requirement cannot be proven with available evidence; a new credential would need approval | Delivery is live-verified. Every remaining Phase 7 check needs a signed-in browser session through the Route, and the run holds no Keycloak user. It must not use a credential not issued to it. Either the user signs in, or approves a run-specific test user. Fixtures (O-6) and a pod restart for the session observation also need approval. |
| 1 | 2026-11-06 ~00:05 EST | 6 entry | Next action needs approval; user decisions required | Delivery needs three merges (Keycloak client box1-gitops#73, Deployment env box1-workloads-dev#90, console operations-console#2). Live acceptance also needs role assignment and approved fixtures. Gaps G-1, G-2 and G-3 need other services. All independent work (Phases 0–5) is finished first, and the open decisions are reported together (`open-decisions.md` O-1…O-9). |

## Repairs

Found during Phase 0 (probe), fixed and retested:

1. **React 19 has no global `JSX` namespace.** The probe's `App(): JSX.Element` failed `tsc --noEmit` locally. Changed to `React.JSX.Element`. This shows the typecheck gate works inside the Maven build.

Found during implementation and local tests (Phase 3), fixed and retested:

2. **Keycloak Dev Services wanted Docker.** Adding `quarkus-oidc` made `@QuarkusTest` try to start a Keycloak container. CI has no container runtime (pilot lesson), and the tests use the WireMock OIDC server. Set `quarkus.devservices.enabled=false`, as asset-service does.
3. **`@Alternative` authentication mechanism hid the test-security mechanism.** My API-aware mechanism (401 instead of a redirect for `/api/*`) was an `@Alternative`, and CDI then dropped every non-alternative `HttpAuthenticationMechanism`, including the `@TestSecurity` ones. Result: 26 tests got 401. It is now a plain bean ranked above OIDC by `getPriority()`.
4. **`quarkus.http.filter.*.matches` with a negative lookahead never applied.** `Cache-Control: no-store` was missing everywhere. Moved the per-path cache headers into a router `headersEndHandler`, and a test now asserts them.
5. **CSRF guard ran after resource matching.** A form-encoded POST got 415 before the guard. The guard is now a pre-matching filter.
6. **The console's own https origin would have been refused by CORS behind the edge Route.** A test sending `Origin: https://operations-console-dev…` exposed it before any deploy. This is the same defect asset-service hit live in run 15 (repair 19). `CONSOLE_PUBLIC_ORIGIN` is now in the CORS origins, and the test profile simulates the http/https mismatch.

Found by verification (Phase 4), fixed and retested:

7. **Login lost the deep link.** The SPA fallback rerouted `/orders/new` to `/index.html` before authentication, so OIDC saved `/index.html` as the restore path and users landed on "Page not found" after sign-in. The fallback now runs at `ROUTE_ORDER_AFTER_DEFAULT`, after security and the static routes. A regression test checks the restore cookie.
8. **Brand link accessible name did not contain its visible text** (axe `label-content-name-mismatch`, WCAG 2.5.3, on every page). Removed the `aria-label`. This is the same class of finding as run 15 repair 7.

Found by reviewer passes (Phase 5), fixed and retested. See `review-findings/` for all 43 findings and their outcomes:

9. **A public client must not carry other services' audiences** (SEC-1). My Keycloak PR would have let any realm user mint inventory and fulfillment tokens by running a PKCE flow themselves. Removed the mappers, and the console now forwards no user token. This is the most consequential finding, and the reviewer caught it before any merge.
10. **Absent values reported as zero** (ARCH-1): when order-service failed, the overview showed "0 exceptions". **An incident invented for any order** (ARCH-2). **ERP detail hidden for EXCEPTION orders** (ARCH-3).
11. **Unconfirmed creates could duplicate** (ARCH-4/FE-4). After a timeout, editing the form or leaving the page minted a new key. The key and values are now locked and kept in sessionStorage. A Firefox test drives a real ambiguous timeout and then a page change, and shows one order.
12. **Polling side effects** (FE-2/FE-3): spinners on pause, data wiped by a failed background refresh, late responses landing on the wrong page.
13. **CSP blocked react-aria's injected stylesheet.** The front-end reviewer had cleared the CSP by reading code. The CSP-violation listener added for FE-10 found it in the first run. Fixed by allowing that exact hash. This is a case where a test the review asked for beat the review's own conclusion.
14. Smaller fixes:
    - ops: log line per failed upstream call, latency timer, page budget for lists, probe cache, bounded metric URIs, runbook rows;
    - release: security gate on, plus a read-only console-smoke step;
    - security: narrower public paths, Idempotency-Key pattern, exact redirect URI;
    - accessibility: table semantics at narrow widths, input contrast, titles, a pause control.
15. **A duplicated YAML key passed the Java tests.** Jackson's YAML parser tolerates duplicate keys; the front end's generator failed on it. The contract loader now uses strict duplicate detection.

Found on the cluster (Phase 6), fixed and retested:

16. **The first gated release failed RHACS on Guava 33.6.0-jre (CVE-2026-102554).** I had turned the gate on (REL-1) without the Guava override that asset-service and inventory-service carry, although discovery recorded that pairing as a run 11 lesson. The user reported it. Fixed in operations-console#3; the second release passed the gate with high findings down from 11 to 10, and nothing was promoted from the failed run.

Found in live acceptance (Phase 7):

17. **Logout left the Keycloak SSO session alive on RH-SSO 7.6.** RH-SSO 7.6 rejects `post_logout_redirect_uri` unless it is a valid redirect URI. My SEC-2 repair had narrowed those to `/callback`, and Keycloak 26 in local e2e honours the separate `post.logout.redirect.uris` attribute, so only the real Route showed it. This is the run 15 lesson "local Keycloak 26.4 is not RH-SSO 7.6", met again in a new place. The fix (box1-gitops#77) awaits approval. Both logout tests now require the SSO session to end.

Test harness and test defects:
- The logout URL carried `?state=`, which my regex did not allow.
- The keyboard test tabbed forward from `main` instead of back into the navigation.
- macOS Firefox's default Tab order skips links; the suite now sets `accessibility.tabfocus=7`, matching a user with full keyboard access.
- My traceparent regex was too strict: flags `03` are valid in W3C level 2.
- The 60 s `/api/info` cache defeated one WireMock `verify`; the cache is intended, so the assertion was removed.
- My ledger updater passed escaped JSON as a regex replacement.

## Profile ambiguity and friction

1. **The prompt's discovery list was partly stale on arrival.** It says the operator did not create `spec.roles` (#59), but #59 was closed as not-a-defect 23 minutes before this run started. It also proposes `box1-ops-console`, while the onboarded repository is `operations-console`. Both were checked rather than assumed.

2. **"Accessible component library" vs native tables.** react-aria-components is used for form controls and buttons. Tables are native `<table>` elements with captions and scoped headers, because the prompt's keyboard criterion (Tab traversal to an order) works more predictably with links in native tables than with a grid's arrow-key model. Recorded here rather than as a decision, since the prompt does not specify it.
3. **"Customer-safe metadata" with no customer data.** No upstream holds names, addresses or contacts; `customerId` is an opaque synthetic ID. The criterion is trivially met today and needs revisiting when real customer data arrives.

## Places I was unsure of my authority

3. **Using the Keycloak user the user issued in chat.** It was explicitly issued to this run, so I used it, for read-only checks only. The password stays out of every file under version control, and I recommended rotating it after the run, since it passed through chat.

1. **`oc apply --dry-run=server` against the KeycloakClient CRD.** The profile prohibits `oc apply` as the deployment mechanism. A server dry run persists nothing, and I used it only to validate the CR schema. Recorded so the user can object.
2. **Closing my own probe PR (operations-console#1).** It was opened as a do-not-merge probe. I closed it after recording the result. It is not a merge and not covered by the approval list.

## Did earlier pilots' lessons prevent repeats?

| Earlier lesson | Applied here | Result |
|---|---|---|
| Check that a release-gate dependency actually works, not just that a pod runs (runs 11, 13) | Proved the Node build in a real PR pipeline before writing the front end | **Prevented.** Proven at 1m17s, before any front-end work |
| PaC takes pipeline definitions from `main` (run 14) | The probe used the template's unchanged `.tekton/`, so its result carries to later PRs | Applied |
| Check host and Podman VM clocks (runs 11, 13) | Checked at 22:49:40 EST: in agreement | Applied |
| Name containers `runNN-*` and never blanket-remove (runs 11, 13) | `run18-keycloak` only; down script removes by name and recorded PIDs; port 18180 (run15-keycloak) avoided | **Prevented.** run15 containers untouched |
| Edge TLS: https redirects and Secure cookies (run 15 SEC-1) | `force-redirect-https-scheme`, `cookie-force-secure` from the start | **Prevented** |
| Own origin refused by CORS behind the edge Route (run 15 repair 19) | Test with own https Origin before any deploy | **Repeated, then fixed** before deploy (repair 6): the lesson was known, but the template's CORS default still bit, and only the test caught it |
| Session cookie authenticating a bearer API (run 15 repair 6) | The console has no bearer API at all; one code-flow tenant | **Prevented by design** |
| Hybrid tenant sends 302 to API clients (run 15 repair 3) | Custom challenge: `/api/*` gets 401 Problem JSON | **Prevented** (tested on every contract path) |
| Roles from `resource_access.<client>.roles` only (runs 12, 15) | `role-claim-path=resource_access/operations-console/roles`; `@RolesAllowed` on resource methods | Applied |
| CI runs `-DskipITs=false` (run 15 repair 16) | `quarkus.test.integration-test-profile=test` from the start; local runs use `-DskipITs=false` | **Prevented** |
| A CSP blocking axe hides failures behind "0 failures" (run 15 repair 17) | The axe spec asserts `passes.length > 0` per page, and failures are listed, not counted | **Prevented** |
| WCAG 2.5.3 button and link names (run 15 repair 7) | axe on 10 views | **Repeated, then fixed** (repair 8) |
| Runtime settings in Deployment env, not ConfigMap literals (run 11) | box1-workloads-dev#90 uses `env`; Argo stayed Synced and smoke passed | **Prevented** (confirmed live) |
| Guava CVE override goes with `security-gates: gate` (runs 11, 15) | Gate enabled in review repair REL-1; the override was not added | **Repeated, then fixed** (repair 16). The lesson was in my own discovery notes; a checklist item tying the gate to known overrides would have caught it |
| Re-read upstream state before relying on it | Re-compared order, inventory and asset main at 23:28 EST: only `.tekton` changed | Applied |

## Environment findings

- **00:3x EST, git slip (mine).** A stray `git checkout run18-guava-cve --` inside a compound command switched branches, so my commit landed on the already-merged local branch and an empty branch was pushed. PR creation failed with "no commits", which exposed it. I moved the commit with cherry-pick and reset the local branch. Nothing wrong was pushed to a PR.

- 23:52–23:59 EST: the workstation's `oc` session returned Unauthorized, then worked again without action from me. That window covered only background polling, and the `gh` PR checks confirmed CI independently. Auth was not touched.

- **23:39 EST, one cause and 14 symptoms.** After a rebuild, every Firefox test failed at sign-in. I read the cause before touching anything:
  - A console JVM that I had started by hand for the session-restart probe (23:20) was still on port 18080. My PID file had recorded the subshell's PID instead, so `local-down` missed the JVM.
  - The new console therefore failed to bind. The old one kept the previous Keycloak container's signing keys, which produced "JWK … not available" and then introspection refused for a public client.
  - Confirmed the process was mine (start time and working directory) and stopped it by PID. `local-up.sh` now refuses to start if the port is busy.
- **The stub server crashed on aborted slow requests**: it read the body after the delay. Fixed. This was also why the "Already placed" check failed in that run.

- 22:49 EST: host and Podman VM clocks agreed.
- The `legacy-erp` VMI restarted at about 22:45 EST. Another run appears active in `legacy-erp-dev`, and this run did not touch it.

- 23:11 and 23:13 EST: host and Podman VM clocks agreed before the e2e runs. No sleep events so far.
- Other runs promoted order-service, inventory-service and asset-service (#86–#88) during this run. Only their `.tekton/release.yaml` changed.

## Building a front end on a Java Golden Path

- The Golden Path task has no Node, but it does have unrestricted egress. A Maven-driven Node install worked first time in CI.
- `frontend-maven-plugin` does not verify the Node archive. Pairing it with `download-maven-plugin` (SHA-256) and a `file://` download root gives the same supply-chain posture the platform applies to Maven itself.
- Generating the lockfile needed the pinned Node: the workstation had Node 25, and `engine-strict` refused it. TypeScript 7 and rolldown ship native binaries as optional dependencies, and the macOS-generated lockfile included the linux-x64 entries.

- The whole front end typechecked and built through Maven on the first try. The friction was elsewhere:
  - OpenAPI typegen pins TypeScript 5, so TS 7 had to give way.
  - React 19 removed the global `JSX` namespace.
- Generating the client from the backend's own OpenAPI at build time needs the contract to exist before Java compiles. A hand-written `META-INF/openapi.yaml`, merged by Quarkus and checked by a drift test, solved that ordering cleanly.
- Serving an SPA from Quarkus with OIDC is subtle: route order decides whether login restores the deep link (repair 7).
- Browser tests cannot run in the Golden Path task (no browser, no containers), so all Playwright evidence is local by construction.

## Consuming other runs' APIs

- Each upstream accepts a different token shape: no auth (order), `aud` only (inventory, adapter), `aud` plus `azp` (asset).
- The order → fulfillment link exists only as an internal naming convention in order-service.
- The fulfillment adapter has no contract in `box1-ops-contracts`, only its served OpenAPI.
- What worked well: every upstream's served OpenAPI matched its repo, all used Problem JSON, and lists used a consistent `Link: rel=next` cursor.
- What made a console hard:
  - No list endpoint has filters or sort.
  - The adapter's status cannot be found from an orderId.
  - asset-service's `azp` pin, a good security choice for its own console, makes it unusable from any other UI without a change.

## Side effects outside the run state

- Clone `/Users/mike/Documents/ChatGPT/box1/run18-operations-console`, plus worktree `run18-docs` of box1-docs.
- Pushed branch `run18-frontend-build-probe` and opened draft PR box1-org/operations-console#1 (`ae245e7`). That PR triggered PipelineRun `box1-ci/operations-console-validate-zqk5s`. Closed it after recording the result.
- Pushed `issue-18-console` and opened box1-org/operations-console#2.
- Opened box1-org/box1-gitops#73 (branch `run18-operations-console-keycloak`, worktree `run18-gitops`) and box1-org/box1-workloads-dev#90 (branch `run18-operations-console-runtime`, worktree `run18-workloads`). Neither is merged.
- Ran one server-side dry run (`oc apply --dry-run=server`) of the KeycloakClient. Nothing was persisted.
- Local: container `run18-keycloak` (port 18280), a Node stub process (18081) and a console JVM (18080), all started and stopped by `src/test/e2e/local-*.sh`. Playwright Firefox was installed into `~/Library/Caches/ms-playwright` (shared cache).
- Four issue comments on box1-docs#18.
- Opened operations-console#3 (Guava). The user merged #73, #90, #2 and #3. Release `-mtdgc` failed at the gate; release `-859h8` promoted via box1-workloads-dev#96 (auto-merged by the pipeline).
- Five reviewer subagents. Two scratch clones (`rev-security`, `rev-ops`), and a prod jar the ops reviewer ran on port 18555, all in the scratchpad.
- One process stopped by PID (12735, my own console from the restart probe, confirmed by start time and working directory).
