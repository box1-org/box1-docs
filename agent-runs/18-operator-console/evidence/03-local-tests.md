# Phase 3–4: local test results

Host clock and Podman VM clock agreed: 23:11:14 / 23:11:15 EST and 23:13 EST before the e2e runs.

## Maven (`./mvnw -B -ntp verify -DskipITs=false`, macOS arm64, Node 24.22.2 verified)

Final local run on the commit before docs (`4af6381` tree):

```
Tests run: 45, Failures: 0, Errors: 0, Skipped: 0      (surefire)
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0       (failsafe, packaged jar)
You have 0 Checkstyle violations.
BugInstance size is 0                                  (SpotBugs + FindSecBugs)
BUILD SUCCESS
```

| Class | Covers |
|---|---|
| ConsoleSecurityTest (9) | Anonymous 401 Problem JSON with no redirect on every contract operation; page navigation 302 with PKCE S256, restoring the deep link rather than index.html; no-role 403 on every role-protected operation; viewer cannot POST or see delivery; CSRF header, JSON and origin checks, including the edge-TLS own origin; CORS never allows `X-Box1-Console` or credentials; smoke paths public with hardening headers; served OpenAPI |
| UpstreamBehaviourTest (13) | HELD shown as waiting with the order label kept; adapter connection reset → "ERP detail unavailable" with no adapter fields; adapter 5 s delay → bounded partial page (<2.5 s); 404 → not yet received; inventory 503 → named partial; order-service down → 503 naming the source for detail, partial for list and overview; filter, sort, page and window; Link `rel=next` host ignored (only the query is reused); idempotent create forwards key, consumer and traceparent and maps replay; 409, timeout and validation mapping; asset 401 → NOT_AUTHORIZED with reason; scenario controller NOT_CONFIGURED; delivery revisions |
| ErpProgressMapperTest (11) | Every adapter combination maps to one stage; HELD is waiting; unknown is unavailable, never guessed |
| ContractDriftTest (1) | Implementation equals contract |
| FrontendServingTest (3) | Index, deep link, hashed asset immutable, other responses no-store, API and /q 404 not rewritten, no third-party host in index.html, brand mark SHA-256 |
| Template tests (8 + 5 IT) | Greeting, info, health, CORS for Developer Hub, OpenAPI, metrics |

## Playwright Firefox (local stack: Keycloak 26.4 container `run18-keycloak`, stubs, built jar)

Run at 23:18 EST, plus the keyboard re-run after its test fix: **14 of 14 passed.**

| Spec | Scenario |
|---|---|
| session | Tokens absent from `document.cookie`, local and session storage, page HTML and `/api/v1/me`; `q_session*` cookies HttpOnly and SameSite=Strict; **only the console and Keycloak hosts contacted** |
| session | Logout → signed-out page, then `/api/v1/me` 401 |
| session | Anonymous GET on all 9 GET paths, and POST, → 401, no redirect |
| roles | No-role user: empty navigation, forbidden state, 403 `ROLE_REQUIRED` on 5 APIs |
| roles | Viewer: no Place order or Delivery; `/orders/new` forbidden; direct POST 403 |
| roles | Developer: delivery revisions |
| roles | CSRF: no header 403, form body 403, foreign Origin 403 |
| flow | Place order → follow → RESERVED → Awaiting ERP (queued, uploaded + outstanding attempts) → accepted → **held (waiting, no failure tone)** → released → adapter shipped while order still FULFILLMENT_REQUESTED (no premature completion) → SHIPPED → COMPLETED (5 timeline entries; evidence links) |
| flow | Same idempotency key twice → one order ("Already placed") |
| flow | Adapter down → "ERP detail unavailable" with the order label |
| flow | Inventory slow, adapter slow, order down, order slow, asset refusal: each a partial page naming the source, within 8 s |
| a11y | axe WCAG 2.0/2.1 A+AA: 0 violations on 10 views (home, orders, place, detail, incidents, incident, sites, delivery, demo, not found) |
| a11y | Keyboard only: skip link → Orders → order → detail (focus moves to main) → Incidents → incident evidence |
| a11y | 390 px: no horizontal overflow on 6 pages |

## Upstream credential use (stub request log)

| Upstream | Calls with bearer | Without | traceparent |
|---|---|---|---|
| order (GET 74, POST 8) | 0 | all | all |
| inventory | 14 | 1 (`/api/info`) | all |
| fulfillment | 12 | 1 (`/api/info`) | all |
| asset | 3 | 1 (`/api/info`) | all |

The user's token goes only to services that accept a token. It is never sent to order-service.

## Session across a restart (local)

Signed in as `vera`: `/api/v1/me` 200. After killing and restarting only the console process, the same cookies got **401**. The log shows Quarkus's "Secret key … auto-generating it" notice. This matches D-003: sessions end at restart until a session key Secret exists (O-3). Live observation comes in Phase 7.
