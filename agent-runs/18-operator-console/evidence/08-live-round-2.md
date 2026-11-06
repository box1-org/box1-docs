# Live round 2 (2026-11-06, America/New_York)

## Decisions taken by the user
The user reviewed the decision list in plan mode:
- A1 merged (#5);
- A2/A3 users issued: `claude` (all console roles) and `loser` (no console role). Credentials are kept only in private mode-600 files and never recorded;
- A4 fixtures and A5 one pod restart approved;
- B2, the held-ERP end-to-end, made the priority;
- B5 favicon approved;
- B6 customer role out of scope;
- C5 replaced by a Developer Hub API-testing ticket;
- the rest backlogged.

## Release of #5
`operations-console-release-ds4rl`: build, security (gate), promote, smoke and console-smoke all Succeeded.
- Image `sha256:e81896a82c48564dfb25c3d4805ac4a33b58a9fe51a99b788d248bdb072f22a4`.
- Promotion box1-workloads-dev#114 → `f334337`. Argo Synced and Healthy.
- `/api/info` gitRef `f202f50` (the #5 merge). SCAN_OUTPUT: critical 0, high 10.

## Live checks
- **403 for a signed-in user without console roles (`loser`), 14:12 EST: PASS.** All 8 GET console API paths and `POST /api/v1/orders` → 403 `ROLE_REQUIRED`. The page shows "no console role" and the forbidden state.
- **`claude` sign-in, 14:10 EST:** RH-SSO required action "Update password" (the password was issued as temporary). The run does not set passwords on a user's account, so the remaining `claude` live checks wait for the user to make it non-temporary.
- **Pod restart (approved, once), 14:16 EST:**
  - Signed in as `loser`, `/api/v1/me` → 200.
  - `oc delete pod operations-console-788459d4c-xtlnn`. The replacement `…-hj6zn` became Ready on the same digest, and Argo stayed Synced and Healthy.
  - The saved session afterwards → **401**: restarts sign users out, as designed until #79.
  - **Finding:** that 401 had an **empty body**. Reproduced with an undecryptable `q_session` cookie on `/api/v1/me`: 401, no content type, empty body (pages still 302 to Keycloak). The page still shows "session ended" for any 401, but the contract promises Problem JSON. Fix planned after the held-ERP E2E.

## Cluster state relevant to the held-ERP E2E (read-only, 14:1x EST)
- The adapter runs `FULFILLMENT_SFTP_ENABLED=true` against `legacy-erp-sftp.legacy-erp-dev.svc` (Service present, 12 h old). VMI `legacy-erp` is Running.
- No order has reached the adapter yet: every order ID → `ful_<suffix>` returns 404.
  - Two orders from 2026-11-05 are still SUBMITTED.
  - Two recent orders from another run's probes (unknown SKU) were REJECTED by inventory within 4 s, so the inventory → order event path works.
- box1-workloads-dev#115 (`CONSOLE_FULFILLMENT_LINK=derived`) is open and needs the user's merge.

## Other outputs
- operations-console#6: favicons (resize-only; hashes asserted) and the live 403 test.
- Backlog issues filed: #78 (order-service `fulfillmentRequestId`), #79 (console confidential client, session key, token strategy), #80 (asset-service accepts console read tokens), #81 (Developer Hub API testing with Keycloak-authenticated APIs).
