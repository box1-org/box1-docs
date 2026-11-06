# Review pass: Security (fresh subagent, operations-console d007f00, box1-gitops#73, box1-workloads-dev#90)

**Summary from the reviewer:** no high-severity issues. The reviewer probed the session, CSRF (10 path-normalisation bypass attempts, all refused), the challenge mechanism, role coverage, SSRF and headers in a scratch clone, and all held.

| ID | Sev | Finding | Outcome |
|---|---|---|---|
| SEC-1 | Med | The proposed public `operations-console` client with `inventory-service`/`fulfillment-adapter` audience mappers would let any realm user mint a token carrying those audiences by running a PKCE flow themselves. That is broader than "only the console backend holds these tokens". It applies to the unmerged box1-gitops#73 and is not live. | **Fixed** in box1-gitops#73 (16d561e): own audience only; console forwards no user token (`CONSOLE_FORWARD_USER_TOKEN=false`). Decision O-9 for forwarding later |
| SEC-2 | Low | Redirect URI wildcard `/*`; only `/callback` is used | **Fixed**: exact `/callback` |
| SEC-3 | Low | The user's token is sent to asset-service (known to refuse it, no audience) and to any configured scenario controller | **Fixed**: no token to asset-service or scenario controller |
| SEC-4 | Low | GET `/logout` can be triggered from sibling `*.box1.org` pages, which are same-site (nuisance: sign-out) | **Accepted and documented** (nuisance sign-out only) |
| SEC-5 | Low | `/q/*` public (swagger-ui, metrics); the template posture; the CSP probably breaks the Swagger UI bootstrap | **Fixed**: only `/q/health*`, `/q/openapi`, `/q/metrics` public; Swagger UI needs a session; test |
| SEC-6 | Info | D-003 says `form-action` includes Keycloak; the config has only `'self'` | **Fixed**: D-003 aligned to the implementation |
| SEC-7 | Info | An odd Link query (space or `#`) or a non-ASCII Idempotency-Key gives 500 instead of a degraded source or a 400 | **Fixed**: IllegalArgumentException degrades the source; Idempotency-Key pattern; tests |
| SEC-8 | Info | `local-up.sh` sets umask after mkdir, the realm file is mode 644, and the Keycloak admin password is visible in `podman inspect` (local and random) | **Partly fixed**: umask first, RUN_DIR must be mode 700. Admin password visible in local `podman inspect`: accepted (random, local) |
| SEC-9 | Info | Public docs describe upstream exposure in more detail than needed; link issues rather than giving detail | **Fixed**: docs link #40/G-2 without exposure detail |

After repairs (operations-console 1d65b2b): full Maven suite 50+5 green; Playwright Firefox 15/15 rerun on the repaired build.
