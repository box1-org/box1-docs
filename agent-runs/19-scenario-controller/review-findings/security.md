# Run 19 scenario controller — Phase 5 security review

Reviewer: security pass (read-only). Date: 2026-11-06 (America/New_York).

Scope reviewed against code:
- `run19-scenario-controller` branch `run19-controller`, `git diff 203968e..e061f6d`
- `run19-inventory-service` branch `run19-fixture-admin`, `git diff 094772a..fca04be`
- Workload manifests `run19-workloads` branch `run19-scenario-controller-runtime` (`workloads/scenario-controller/*`) and Keycloak clients `run19-gitops` branch `run19-scenario-controller-keycloak` (`platform/identity/keycloak/realm/scenario-controller*-client.yaml`). These were read only for RBAC and identity context.
- Evidence scripts `run19-docs/agent-runs/19-scenario-controller/evidence/scripts/{stack.sh,realm.sh,e2e.py}`
- Requirements `09_scenario_controller.md`, `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`, decisions D-006 and D-009

No Secret values were read. `postgres.yaml` holds a Secret that contains only `replace-before-sync` placeholders. Only its keys were inspected.

**Verdict:** no Critical or High findings. Authorization, the azp/role handling and the two-gate allowlist are implemented correctly and fail closed. The controller needs no Kubernetes RBAC. One Medium design gap: the allowlist gates where the controller runs, not where its effects land. Several Low and Info items follow.

---

## Findings

### SEC-1 — Medium — The allowlist gates the controller's own namespace, not the target services
- **Where:** `src/main/java/org/box1/scenario/Gate.java:29-39`; `ScenarioSettings.java:21-25`; `application.properties:40-42`
- **Issue:** `Gate.refusal()` checks only `POD_NAMESPACE` against `SCENARIO_NAMESPACE_ALLOWLIST`. The order, inventory, adapter and token URLs come from config and are never compared with any allowlist. `SCENARIO_ENVIRONMENT` is only a label: it is recorded but never checked. The requirement asks for an "explicit namespace/environment allowlist", and boundary doc 06 permits fault injection and data reset "only ... in a named demo namespace/environment".
- **Scenario:** A controller deployed correctly in `scenario-controller-dev` has its `INVENTORY_SERVICE_URL` or `ORDER_SERVICE_URL` set, by edit or copy/paste in a later overlay, to `*-prod.svc` or another environment's route. Both gates pass. Seed, reset (restock) and scenario orders then land in the non-demo service, and the audit records `namespace=scenario-controller-dev`, so the trail looks compliant.
- **Fix:** Add a target gate. Parse each upstream base URL and require the host form `<svc>.<ns>.svc[.cluster.local]` with `<ns>` in a `SCENARIO_TARGET_NAMESPACE_ALLOWLIST`, or require an exact match against an allowlist of base URLs. Fail at startup, or refuse every action, when a target does not match. Record the target hosts in the START/SEED audit detail. Optionally refuse unless `SCENARIO_ENVIRONMENT` is in an environment allowlist. Add a test that uses an off-list target URL.

### SEC-2 — Low — The namespace identity can be overridden through config, not only through the downward API
- **Where:** `application.properties:35` (`scenario.namespace=${POD_NAMESPACE:}`); `ScenarioSettings.java:15`; `Gate.java:20-22`
- **Issue:** The value is a normal SmallRye config property. Any higher-ordinal source overrides the `${POD_NAMESPACE}` expansion: the `SCENARIO_NAMESPACE` environment variable (ordinal 300), `-Dscenario.namespace`, a `.env` file, or `config/application.properties` in the working directory. `GateTest` itself relies on this, overriding `scenario.namespace` to `payments-prod`. The Deployment uses `envFrom: configMapRef scenario-controller-config`, so adding `SCENARIO_NAMESPACE=scenario-controller-dev` to the generated ConfigMap of a copy deployed elsewhere makes that copy claim the allowlisted namespace. D-006 says the namespace "comes from the downward API", which is therefore not strictly enforced.
- **Scenario:** Someone copies the kustomization to a non-demo namespace and adds `SCENARIO_NAMESPACE` "to fix the refusal". The gate passes.
- **Fix:** In `Gate`, read `System.getenv("POD_NAMESPACE")` directly instead of through config. Alternatively, fail at startup when `scenario.namespace` has a config source other than the `POD_NAMESPACE` expansion, for example by checking `ConfigValue.getSourceName()`. Keep the test override through a dedicated test-only hook.
- **Residual (accepted):** The allowlist and `POD_NAMESPACE` come from the same Deployment, so the gate protects against misconfiguration and copies, not against a malicious deployer. Record this limitation in the runbook.

### SEC-3 — Low — The audit actor is `preferred_username` (or `upn`), not the immutable subject, and can collide with the system actor
- **Where:** `api/ScenarioResource.java:99-102`; `api/RunResource.java:108-111`; system rows use the literal `"scenario-controller"` at `run/Engine.java:289, 294, 341`
- **Issue:** `JsonWebToken.getName()` resolves `upn`, then `preferred_username`, then `sub`. Keycloak usernames are realm-assigned and mutable, and they can be user-editable if the realm allows username editing. A realm user named `scenario-controller`, or a `upn` mapper, would produce operator rows that cannot be told apart from the controller's own RESULT/RESET rows. Renaming a user also breaks attribution across the 90-day retention. `docs/architecture.md:53` says the actor is the "token subject", which is not what the code records.
- **Scenario:** An operator whose username equals `scenario-controller` stops runs. The audit attributes the stops to the system.
- **Fix:** Store `sub` as the actor ID and `preferred_username` as a separate display column. Alternatively, prefix human actors (`user:<name>`) and reserve `system:scenario-controller`. Make the docs match. Note that the CLI client's `defaultClientScopes: [profile, roles]` omits Keycloak's `basic` scope, which carries `sub` in Keycloak 25+. Whether cluster CLI tokens contain `sub` is **not established**. Verify this before relying on `sub`.

### SEC-4 — Low — The controller's service identity holds the broad `inventory-admin` role
- **Where:** `run19-gitops .../scenario-controller-client.yaml:41-48`; inventory `AdminResource.java` (class-level `@RolesAllowed("inventory-admin")` on create site, create stock, restock and release reservation)
- **Issue:** The controller restricts itself to fixture IDs in code (`FixtureService.restore` checks `Fixtures.isFixtureStock`, and the IDs are constants). The token it holds, however, can restock any SKU at any site, create arbitrary permanent sites and stock records (there is no delete route), and release any reservation. If the controller pod is compromised or the client secret leaks, that is full inventory admin. The new create-once routes are also not limited to fixture IDs: any `site_*` and any SKU are accepted.
- **Fix:** A follow-up, since D-009 accepted the current design. Add a narrower inventory role, for example `inventory-fixture-admin`, limited on the inventory side to create-once and restock for an allowlisted fixture prefix or ID set, with no release. Alternatively, have inventory reject non-fixture IDs for that role. Track this in the backlog.

### SEC-5 — Low — Role refusals (401/403) are not in the audit trail
- **Where:** `api/ProblemMappers.java:29-42`; `run/Engine.java:325-336` (only gate and catalog refusals are audited)
- **Issue:** `@RolesAllowed` rejects viewers and no-role tokens that try start, stop, reset or seed before `Engine` runs, so the attempt is never written to `scenario_audit`. The run's own verification list includes "request without the role", and doc 06 asks for "a complete audit trail of invoked scenarios".
- **Fix:** In the `ForbiddenException` mapper, or in a request filter for `POST /internal/v1/**`, write a `DENIED` audit row with the caller's `sub`/name, the action and the path template. Do not echo the raw path. Rate-limit or aggregate if needed (see SEC-8).

### SEC-6 — Low — Error details can carry internal text to callers and into the audit
- **Where:** `run/Engine.java:176-178` (`"Seeding failed: " + plain(error)`), `run/Engine.java:309-311`, `run/Engine.java:243-244, 362-365`
- **Issue:** `plain()` returns any `RuntimeException` message. Caller-visible examples:
  - internal service hostnames ("Call to inventory-service.inventory-service-dev.svc failed");
  - `RunStore.StoreException` "Audit store failure: <SQLSTATE>", when caught inside `seed()` (the audit write in the catch block then probably fails as well);
  - Java 21 helpful NullPointerException messages that describe internal code, for example `InventoryApi.restock` dereferencing a null body at `InventoryApi.java:60-61`.

  Untrusted request input is never echoed: names are regex- and catalog-checked first, and run IDs are not echoed. Exposure is limited to operators.
- **Fix:** Map only `UpstreamException` and `InventoryToken.NotConfigured` messages to caller and audit text, and use a fixed string ("internal error; see logs with correlation <id>") for everything else. Let `StoreException` reach its 503 mapper instead of being rewrapped as 502. Null-check `reply.body()` in `restock`.

### SEC-7 — Low — Concurrent resets can over-restock fixtures (TOCTOU)
- **Where:** `run/Engine.java:149-166`; `fixtures/FixtureService.java:54-72`
- **Issue:** A reset without an open run takes no lock and generates a fresh `resetId`, so each concurrent reset reads `available` and restocks the difference under a different idempotency key. Two parallel `reset` calls, or a reset that races a `start` of the same scenario, push stock above the opening quantity or add stock in the middle of a run. A reset during a "Trouble with Tribbles" run, for example, can create a second tribble and break the "exactly one reservation" evidence. Fixture-only and operator-only, so this is an integrity issue, not an escalation.
- **Fix:** Serialize standalone resets with the same mechanism as runs: a DB advisory lock, or a short "reset" row under the one-open-run index. Refuse a standalone reset while any run is open (409). Alternatively, derive the idempotency key from the current stock version.

### SEC-8 — Low — The operator can grow the audit store without limit
- **Where:** `run/Engine.java:318-336`; schema `V1__scenario_schema.sql` (append-only trigger, 90-day retention)
- **Issue:** Every `start`/`stop`/`reset` of an unknown, not-yet-possible or not-allowed scenario writes a `DENIED` row, and nothing limits the rate. The 4K body limit and the regex-bounded name cap row size, but not row count, and the rows cannot be deleted for 90 days. Requires the operator role, so impact is limited to a lab.
- **Fix:** Add a simple per-actor rate limit or collapse identical consecutive denials. A low priority.

### SEC-9 — Low — The CLI exposes the bearer token in the process list
- **Where:** `scripts/scenario.sh:12` (`-H "Authorization: Bearer ${TOKEN}"` passed as a curl argument)
- **Issue:** On a shared host, other local users can read the token through `ps`/`/proc/<pid>/cmdline` while curl runs. Injection was checked and is fine: the name, run ID and TTL are regex-validated before interpolation, the JSON body is built only from validated digits, there is no `eval`, `watch` passes the response through stdin to `python3`, and there is no `-L`. Two minor points: `SCENARIO_URL` is not checked for `https://`, so a mistyped `http://` URL sends the token in cleartext, and the header comment and `docs/runbook.md:22` say the token is "for client scenario-controller", while the cluster accepts `azp=scenario-controller-cli` only.
- **Fix:** Pass the header through stdin, for example `curl -H @- <<<"Authorization: Bearer $TOKEN"` (curl ≥ 7.55) or `-K -`. Refuse a non-https `SCENARIO_URL` unless it is localhost. Correct the client name in the script and the runbook.

### SEC-10 — Low/Info — Outbound credential transport and token-URL handling
- **Where:** `upstream/InventoryToken.java:50-55`; `upstream/Http.java:47-68`; Deployment env (`INVENTORY_SERVICE_URL=http://...svc:8080`)
- **Issue:**
  - The token URL comes from config only, so callers have no SSRF path. Its scheme is not enforced, so a misconfigured `http://` token URL would send the client secret in cleartext. The cluster value is `https://keycloak.apps.ocp.box1.org/...` (correct).
  - The `inventory-admin` bearer token goes to inventory over plain in-cluster HTTP. This matches the existing platform pattern, but it remains a cleartext admin credential on the pod network.
  - `URI.create` and the `indexOf("//")` parsing tolerate odd values. This is harmless because the URL is config-only.
- **Fix:** Require `https` for the token URL except loopback, and validate the URL at startup with `URI.create`, checking scheme and host. Track in-cluster TLS or mTLS for admin calls as platform follow-up.

### SEC-11 — Info — Upstream response bodies are read without a size cap
- **Where:** `upstream/Http.java:67, 81` (`BodyHandlers.ofString()`)
- **Issue:** A compromised or buggy upstream, including the `/q/metrics` text fetch, could return a very large body. The pod has `-XX:+ExitOnOutOfMemoryError` and a 512Mi limit, so the result is a restart, and run recovery then aborts and resets. Only internal fixed upstreams are involved.
- **Fix:** Use a bounded body handler, for example by limiting through `BodyHandlers.ofInputStream()` and reading at most 1 MiB.

### SEC-12 — Info — The append-only audit relies on triggers the app's own DB role can drop, and the hard-coded 90 days conflicts with configurable retention
- **Where:** `V1__scenario_schema.sql:42-59`; `run/Engine.java:212-216`; `application.properties:46`
- **Issue:** Flyway and the app use the same DB user (the table owner), which can `DROP TRIGGER`. The triggers stop application bugs, not a compromised app. Separately, if `SCENARIO_AUDIT_RETENTION` is set below 90 days, the purge `DELETE` hits the trigger exception and the whole retention job fails.
- **Fix:** For the lab, document both points. If needed later, split the migration owner from the runtime role, give the runtime role only INSERT/SELECT on `scenario_audit`, and validate `retention >= P90D` at startup or derive the trigger interval from config.

### SEC-13 — Info — Anonymous smoke paths
- `/q/openapi` and `/q/swagger-ui` (`quarkus.swagger-ui.always-include=true`) publish the internal API shape on the public Route. This is an intended D-009 decision, and no credentials or examples with tokens appear.
- `/q/metrics` exposes `scenario_runs_total{scenario,outcome}`, `scenario_refusals_total{action}`, `scenario_active_runs`, JVM metrics and HTTP metrics with templated URIs. No actors, run IDs or fixture data are exposed. Acceptable.
- `/q/health/ready` returns `sqlState` when the DB is down (`DatabaseReadinessCheck.java:39`). Minor.
- `/api/info` returns the git ref and Java feature version, which is intended.
- `/api/greetings?name=` (template leftover, `GreetingResource.java:30`) reflects the query value in a JSON body. Because the content type is JSON, this is not an XSS sink. It is pre-existing template code. Consider removing it.
- No Kubernetes, Secret or config-dump endpoints exist, and `/q/dev` is not active in prod.

### SEC-14 — Info — Test coverage gaps for the security properties
- `GateTest` covers only "namespace not on the list". The code handles these correctly by inspection, but they have **no tests**: unset or blank `POD_NAMESPACE` → `unknown` → refused; `SCENARIO_CONTROL_ENABLED=false`; an empty allowlist; an allowlist containing `unknown`; and the `SCENARIO_NAMESPACE` override (SEC-2).
- `SecurityTest` covers the azp mismatch (`otherClient`) and groups-only tokens. A token with no `azp` claim is not covered, and the code correctly gives it no roles.
- Local e2e (`realm.sh`) issues tokens from the confidential `scenario-controller` client, with direct grants and its own audience, under the default `SCENARIO_ALLOWED_AZP=scenario-controller`. The cluster configuration (`azp=scenario-controller-cli`, a public client with device/PKCE flows, and audience and roles through scope mappings) was **not exercised**. Live acceptance should include a positive CLI-token call and a negative token from another client.

### SEC-15 — Info — Evidence scripts in the public box1-docs repo
- `stack.sh`, `realm.sh` and `e2e.py` contain **no secrets**.
  - The Keycloak admin password, client secret, user password and SSH key are generated with `openssl rand`/`ssh-keygen` into the scratch `WORK` directory and are read with `$(cat ...)` at runtime.
  - The only literal credential is `postgres`/`postgres` for a throwaway local container bound to `127.0.0.1`. This is acceptable for the lab, but say so in a comment.
  - A scan of the run-19 evidence directory for JWTs (`eyJ…`), hex client secrets and private-key headers found nothing.
- Minor points:
  - The scripts embed absolute workstation paths (`/Users/mike/...`, `/private/tmp/claude-501/...`), which reveal the local username and session layout.
  - `stack.sh:22-34, 88-89` passes the client secret and password as process arguments (`env ... INVENTORY_TOKEN_CLIENT_SECRET=...`, `curl -d client_secret=...`), and `token-*` prints tokens to stdout. All of this is local and short-lived.
  - `e2e.py` captures tokens through `subprocess` and states that it never prints them. Its log lines were not seen to print them.
- **Fix (optional):** Parameterize `WORK`/`BOX` through environment variables, and pass secrets with `--data-urlencode @file` or stdin.

---

## Verified no-finding areas

| Area | Result | Evidence |
|---|---|---|
| AuthN/AuthZ on every `/internal` path | Every method on `ScenarioResource` and `RunResource` has `@RolesAllowed`. Reads accept viewer or operator; start, stop, reset and seed require operator. No other resource is under `/internal`. Enforcement is in the backend, not the UI. | `ScenarioResource.java:46,59,75,89`; `RunResource.java:44,57,74,90,102`; `SecurityTest` 401/403 matrix |
| JWT verification | Issuer, audience `scenario-controller` and the JWKS signature are verified, and expiry is enforced by default. ID tokens (aud = CLI client) and Keycloak refresh tokens are rejected. Lazy auth (`proactive=false`) leaves anonymous smoke paths unaffected. | `application.properties:55-61`; `SecurityTest.badTokensAreRejected` |
| Roles only from `resource_access.scenario-controller.roles` | The augmentor builds a **new** identity without copying the original roles, so top-level `groups` and other clients' roles are dropped. | `ClientRoleAugmentor.java:39-55`; `SecurityTest.rolesFromAnotherClientOrTheGroupsClaimAreIgnored` |
| azp allowlist | A missing or unlisted `azp` gives an authenticated identity with **no roles**, which results in 403. `SCENARIO_ALLOWED_AZP` is required config: an empty value fails startup. Cluster value: `scenario-controller-cli` only. | `ClientRoleAugmentor.java:41-44`; `ScenarioSettings.java:40`; Deployment env |
| Two-gate allowlist fails closed | Control defaults to `false`. Unset or blank `POD_NAMESPACE` → `unknown` → refused, even if `unknown` is listed. A missing allowlist → empty → refused. Matching is exact. Gate refusals are audited and return a plain 403 before any upstream call (GateTest asserts no writes reached a service). Seed is gated too (`allowed("fixtures", "SEED", …)`). Caveats: SEC-1, SEC-2. | `Gate.java:20-39`; `Engine.java:93,135,151,170`; `GateTest` |
| No exec, shell or arbitrary URL fetch | No `ProcessBuilder`/`Runtime.exec` and no Kubernetes client. All outbound calls go through `Http` with config base URLs and constant paths. Every caller- or upstream-derived segment passes `^[A-Za-z0-9_-]{1,128}$`, and the query string is built only from validated segments. Order IDs from upstream are re-validated (`ORDER_ID`). Redirects are `NEVER`, and every call has a timeout. | `Http.java:26,40-45,34`; `InventoryApi.java:28,43,48,55`; `OrderApi.java:17,40,47,56`; `AdapterApi.java:29,44` |
| SSRF | No request field reaches a URL, host, header name or path. Request inputs are only the scenario name (regex plus catalog), `ttlSeconds` (bounded by catalog max ≤ 3600), run ID (regex) and `limit`/`before` (bounded). | as above; `ScenarioResource.java:105-110`; `RunResource.java:65,82,113-121` |
| Client secret and token caching | The secret is used only in the form body to the token endpoint. Nothing logs headers or bodies. Errors carry status and host only. The access token is cached in memory under `synchronized`, refreshed 30 s before expiry, and never stored, audited or returned. | `InventoryToken.java:43-63`; `UpstreamException.java`; `Http.java:69-73` |
| Error responses | All mapped to RFC 9457. Parser, JSON and framework 400s give fixed text. 401 and 403 give fixed text. Store failures give a fixed 503 and log only the SQLSTATE. Unknown or malformed names get a fixed 404 that does not echo the name. Unmapped exceptions fall back to the Quarkus prod 500, which shows no stack trace. Caveat: SEC-6. | `ProblemMappers.java`; `SecurityTest.unknownAndMalformedNamesGetAPlain404` |
| Body limits and unknown fields | `max-body-size=4K`, `fail-on-unknown-properties=true`. The start body accepts only `ttlSeconds`. | `application.properties:22-23`; `Views.Start` |
| Audit field forgery | Callers control no audit field other than through their token identity. Environment and namespace come from config. Detail text is built from validated or constant values. SQL is fully parameterized. The schema enforces append-only. Caveats: SEC-3, SEC-12. | `RunStore.java:115-133`; `V1__scenario_schema.sql` |
| One run at a time and polling bounds | The partial unique index `ux_scenario_run_one_open` serializes starts across threads and replicas. `RunContext.await` ends at the earlier of TTL and its limit, checks stop on each iteration and sleeps `poll` between probes. The sweep ends runs past TTL plus 30 s grace. Startup recovery aborts and resets orphaned runs. The catalog caps TTL at 3600 s. Caveat: SEC-7 (standalone reset is not serialized). | `V1__scenario_schema.sql:24`; `RunStore.insert`; `RunContext.java:118-138`; `Engine.java:183-209`; `Catalog.java:58-61` |
| Inventory create-once routes | Class-level `@RolesAllowed("inventory-admin")`; site regex, SKU regex (no control characters), status enum, reason 1–200 characters without control characters, `openingQuantity` 0–1,000,000, null-body check, 16K body limit, unknown fields rejected. Inserts use `ON CONFLICT DO NOTHING`. They never update or delete, and a conflict returns 409 without changing data. The actor is the token `sub`. `site_registration` is immutable, with at most one OPENING movement per record. Logs contain only the validated `siteId`. Caveat: SEC-4 (scope of the role). | inventory `AdminResource.java:34-98`; `Validation.java`; `ReservationService.java:+236-269`; `InventoryStore.java:+377-452`; `V3__…sql` |
| RBAC | **The controller needs no Kubernetes RBAC and nothing assumes it.** `automountServiceAccountToken: false` is set on both the ServiceAccount and the pod spec. The `scenario-controller` SA's only binding is `system:image-puller` in `box1-ci` (image pull). The `release-observer` Role and RoleBinding bind `box1-ci/ci-observe`, not the controller. The code has no Kubernetes client, and the VM-level and platform scenarios (`erp-unavailable`, `broker-outage`, `poison-event`, `bad-artifact-gate`) are `NOT_YET_POSSIBLE`. The pod runs under the `restricted` PSA level with non-root, all capabilities dropped and a read-only root filesystem. The Route uses TLS edge with redirect. A NetworkPolicy restricts Postgres ingress to the controller. | `deployment.yaml:27-33,113-117`; `serviceaccount.yaml:6`; `onboarding.yaml:15-94`; `namespace.yaml:7`; `scenarios.yaml:88-142` |
| CORS and CSRF | A single origin (Developer Hub), credentials disabled, bearer-only auth with no cookies, so no CSRF surface. | `application.properties:17-21` |
