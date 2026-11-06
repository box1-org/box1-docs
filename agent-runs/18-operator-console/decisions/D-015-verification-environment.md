# D-015 Verification environment and proof levels

**Status:** decided.

- **Unit and integration tests in CI** (`mvn verify` in the Golden Path task, with no container runtime): `@QuarkusTest`, with `OidcWiremockTestResource` for the code flow and WireMock-backed REST stubs per upstream (`quarkus-junit` plus WireMock). This covers 401/403 on every API path, CSRF, partial sources, timeouts, the ERP mapping, idempotent submit pass-through and the OpenAPI drift check.
- **Local browser tests:** Playwright **Firefox** only, from `src/main/webui/e2e/`. They run against the console in dev/prod mode on the workstation, signing in through a local Keycloak container (`run18-keycloak`) and using controllable upstream stubs (`run18-stubs`). They cover login, token absence, logout, keyboard traversal, axe scan, 390 px width, no third-party hosts, partial pages, and held/shipped/rejected rendering.
  - Proof level: `locally_tested`.
  - Local Keycloak is not RH-SSO 7.6 (run 15 lesson). The real-Route sign-in is proven separately in Phase 7.
- **Cluster:** a real Route, real Keycloak and real upstreams after delivery (`live_verified`). A held ERP request cannot be produced on the cluster today (G-3).
- **Not run in CI:** Playwright, because the task has no browser. It is recorded as local evidence.
