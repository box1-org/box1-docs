# Security pass (covers the console page and the Route)

Fresh read-only subagent, given the diffs, prompt and profile; not the implementation reasoning. 2026-11-05 ~19:35 EST. Findings concern this run's unmerged code. One observation about live shared infrastructure was reported to the user directly and is recorded here as a pointer only.

SEC-1 (medium) The app does not know it is behind edge TLS: the code flow builds http:// redirect_uri (Keycloak registers only https://, so console login would fail on the cluster), session cookies lack Secure, no HSTS. Local tests on plain HTTP cannot catch it.
SEC-2 (medium) Any box1 realm user can obtain an asset-service token through the public client (own PKCE, code from their own browser) and read readings and alerts, which need no role.
SEC-3 (low-medium) Tokens issued to other clients for a user who holds asset-service roles carry aud asset-service (Keycloak roles scope); the API checks aud but not azp.
SEC-4 (low-medium) No frame-ancestors/X-Frame-Options/CSP/nosniff/referrer headers; SameSite=strict is site-scoped (*.box1.org), so a same-site page could frame the console.
SEC-5 (low) Session encryption key generated per JVM: sessions end on restart and rollout; more than one replica breaks login.
SEC-6 (low) Tenant resolver and HTTP permission match control paths differently (exact /api/v1/control, matrix params). No escalation found.
SEC-7 (low) Runs can starve real ingestion through the shared bucket (as ARCH-2); load runs ungated (as ARCH-13).
SEC-8 (low) Armed runs and refusal audit rows unbounded per actor.
SEC-9 (info) Audit trigger bypassable by the owning role (as PERS-9); audit stores preferred_username, not sub; /q/* permit wider than smoke needs (swagger-ui); GET logout; relative asset paths at /console without slash; PostgreSQL pod without explicit securityContext; Kafka trust boundary: pointer only, reported to the user.

Verified OK (reviewer): deny-by-default; CORS; console tenant PKCE and 499; path-only tenant selection; roles only from the client claim and audience checked; CSRF header plus JSON; no XSS sinks; redirect scope; confirmation token handling; run bounds and gate; chaos scope; input bounds; no leakage in errors/logs; no secrets in source; workload securityContext and NetworkPolicy.

## Outcomes (asset-service 7cdc138, gitops b313754, workloads bb0bcae)

| Finding | Outcome |
|---|---|
| SEC-1 | Fixed. `force-redirect-https-scheme` and `cookie-force-secure`; HSTS. Test `HttpsRedirectTest` (https redirect_uri, Secure cookie). Cluster login not yet exercised. |
| SEC-2 | Fixed. Reads need `telemetry-reader`, `telemetry-writer` or `chaos-operator`; role added to the client CR. Test `readsNeedATelemetryRole...`. |
| SEC-3 | Fixed. `required-claims.azp=asset-service` on both tenants. Test with an `openshell-cli` token shape. |
| SEC-4 | Fixed. CSP (frame-ancestors none), X-Frame-Options DENY, nosniff, no-referrer, no-store on console and sign-out. Test. Browser checks rerun. |
| SEC-5 | Recorded as a known limit (single replica; sessions end on restart). A Secret-backed key needs approval. |
| SEC-6 | Fixed. Resolver matches any path starting with the console or control prefix. |
| SEC-7 | Fixed (see ARCH-2, ARCH-13). |
| SEC-8 | Fixed in part: open arms capped at 4. Per-actor rate limit of refusals not added. |
| SEC-9 | Partly fixed: PostgreSQL securityContext added; TRUNCATE guard. Swagger UI kept public as the Golden Path template does; GET logout and `sub` in audit recorded. Kafka trust boundary: reported to the user. |
