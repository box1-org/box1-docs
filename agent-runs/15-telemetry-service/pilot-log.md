# Frontier profile pilot log: box1-docs#15

No comparison with `qwen-64k`, because no baseline exists.

## Stops

| # | Time (America/New_York) | Phase | Stop condition | Reason |
|---|---|---|---|---|

Phase 0 found four items that need the user (D-013 to D-016) plus approval-gated work (D-012). Per the run request, a stop blocks only dependent work, so these are being collected for one report while independent work continues. None blocks design, contracts, local implementation or verification.

## Repairs

Found during implementation and local tests (Phase 3), fixed and retested:

1. **Hysteresis that never fired.** My first engine reset the breach count on readings inside the hysteresis band, so a value flapping across the warning level never raised an alert, the opposite of "one alert then one clear". Caught while writing the test, before code depended on it (D-008 records both versions).
2. **Chaos shifted the load sequence.** Burst extras drew values from the load stream, so the same seed gave different load values with and without chaos. Extras now have their own stream; a test checks base values survive chaos (D-005).
3. **Hybrid OIDC redirected API clients.** With one hybrid tenant, an anonymous `POST /readings` got a 302 to Keycloak, not a 401; path-level `auth-mechanism` and resource annotations did not change that. Split into a bearer-only default tenant and a `console` code-flow tenant by `tenant-paths`.
4. **A meter registration error wedged the consumer.** The clear path registered `asset.alerts.transitions` with different tag keys from activation; Prometheus threw, and the consumer retried the non-transient error forever, holding the partition. Fixed the tags, and the consumer now retries only transient database errors indefinitely; anything else gets five attempts and is dead-lettered as `PROJECTION_FAILED`. This is the same defect class the inventory reviewers found (permanent errors retried), reached by a different route.
5. **Config keys that would break startup.** The strict `asset.*` mapping would have rejected the scheduler interval keys if anyone set them. Moved them under `box1.*`.

Found by verification (Phase 4), fixed and retested:

6. **A console session cookie authenticated the bearer-only API.** Against the real app, anonymous data-API calls from a client that had visited `/console/` got a login redirect, not 401. Quarkus picked the `console` tenant from the session cookie ahead of `tenant-paths`, so a logged-in browser could authenticate reads and, with `telemetry-writer`, ingestion: a CSRF surface the design ruled out (D-002). The WireMock tests had sent no cookies, so they passed. A path-only `TenantResolver` fixed it, and a test now sends console cookies to the data API.
7. **Accessibility and narrow layout.** axe-core found 20 buttons whose accessible name did not contain their visible text (WCAG 2.5.3), and the page overflowed 116 px at 390 px, from crushed tables and a fieldset's `min-width: min-content`. Both fixed, then rerun clean.

Test harness and test defects: wrong expected codes for a form post (415 is a refusal too) and an expired arm (409 once the reaper closed it), non-hex run IDs in a reaper test, a URL-encoding mistake, a deleted test file from a failed split script (recreated), and the `latest`-offset race in a fresh test group (tests now wait for a probe reading). In Phase 4: the metric parser read OpenMetrics exemplar timestamps as counter values (printing 1.79 billion rejections), a rejection scenario relied on counters that an app restart had reset, and a test reader scanned the whole local topic from the beginning and timed out once earlier runs had filled it.

## Profile ambiguity and friction

1. **The prompt's discovery bullet was already stale on one point.** It says `postgres.yaml` "is from the same template pattern as the database credential issue". It exists but is empty and unreferenced: asset-service was onboarded with PostgreSQL off, so there is no database or Secret at all. The "verify before relying on it" note covered this.

## Places I was unsure of my authority

1. **Standing memory for `developer-hub` sync.** Workspace memory holds a standing approval to sync that Application. This run's instruction says Argo syncs need explicit approval one at a time, and that narrower instruction wins, as in the inventory run.

## Did earlier pilots' lessons prevent repeats?

| Earlier lesson | Applied here | Result |
|---|---|---|
| Permanent errors retried forever (inventory review) | Retry loop written to hold on database failures | **Repeated, then fixed in Phase 3.** My loop retried every exception; a meter-registration bug wedged a partition. Now transient-only, with a bounded path to the DLQ. |
| One cause looks like many failures (order, inventory) | Read causes before counting | **Prevented misdiagnosis.** 5 failures: 3 test defects and 1 product defect. |
| Exemplar timestamps parsed as metric values (inventory saga script) | Not applied: I did not reread that note before writing the parser | **Repeated.** Caught because the number was implausible. |
| ConfigMap literal changes fail promote (#42) | New settings are Deployment `env` entries | Applied; promote not yet exercised |
| Guava CVE fails the gate; template gate disabled (#42) | Guava override and `security-gates: gate` from the start | Applied; gate not yet exercised |
| Roles from a top-level `groups` claim (inventory review) | `role-claim-path` only; a test sends roles in `groups` and expects 403 | **Prevented.** |
| Role check after body binding gives 400 not 403 (inventory) | Path policy plus `@RolesAllowed`; tests assert 403 with invalid bodies | **Prevented.** |
| DLQ topic must exist first (order, inventory) | Separate PR and documented merge order | Applied; not yet merged |
| Don't publish live weaknesses (order) | Discovery findings reported to the user directly; pointers only | Applied |
| Check that a release-gate dependency actually works (order) | Not yet: Phase 6 | Pending |
| Laptop sleep | `caffeinate -ims` on every long run; clocks checked before each | No sleep observed so far |
| Clock domains (order) | Run timing, heartbeats, reaper and outbox use the database clock | No clock-domain defect found so far |
| Start reviewers after Phase 4 (inventory) | Reviewers start after this commit | Applied |

## Environment findings

- The first containers run showed 5 failures; reading them gave 3 test defects and 1 product defect behind the other 2. The earlier pilots' "one cause looks like many" lesson applied directly.

- Host and Podman VM clocks agreed at 23:04 UTC at start.

## Side effects outside the run state

- Local containers `run15-pg` (postgres:15-alpine, port 15432), `run15-kafka` (apache/kafka 4.2.0, port 19092, topics created locally) and `run15-keycloak` (quay.io/keycloak/keycloak:26.4, pulled, port 18180, realm generated from the proposed KeycloakClient with two local-only users). Local app on port 18080.
- Pushed branches: `telemetry-service` (asset-service), `asset-service-v1` (box1-ops-contracts), `telemetry-dlq-topic` and `asset-service-keycloak-client` (box1-gitops). New worktrees `run15-contracts`, `run15-workloads`, `run15-gitops`. No PRs opened yet, so no CI has run.

- `git fetch` in the user's `box1-docs` clone (no prune; checkout, branch and untracked file unchanged). The discovery subagent ran `git fetch` in the `box1-gitops`, `box1-ops-contracts`, `box1-workloads-dev`, `box1-templates`, `quarkus-reference` and `inventory-service` clones.
- New worktree `run15-docs` (branch `agent-run/15-telemetry-service`). New clone `run15-asset-service`. Discovery subagents cloned asset-service and extracted white-paper images into the session scratch directory.
