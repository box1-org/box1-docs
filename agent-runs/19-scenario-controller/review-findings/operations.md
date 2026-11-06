# Operations review: scenario-controller, run #19

Scope: `run19-scenario-controller` branch `run19-controller` at `e061f6d` (`git diff 203968e..e061f6d`), and the GitOps manifests on `box1-workloads-dev` `origin/main` under `workloads/scenario-controller/`. This was a read-only pass. Live cluster reads were limited to `oc get`, `oc adm top` and events in `scenario-controller-dev`. No Secret values were read. The pod running there is still the template build `203968e` (143Mi, healthy), so I did not observe any runtime behavior of `e061f6d`.

## Findings

### OPS-1 (Medium): a rolling update aborts and resets a run that the old pod is still executing

- Code: `src/main/java/org/box1/scenario/run/Engine.java:193-209` (`onStart` → `recover`) and `:218-223` (`onStop` only sets the flag).
- GitOps: `workloads/scenario-controller/deployment.yaml:13-17` uses `RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0`.
- Failure scenario:
  1. Automated dev promotion merges while a run is active.
  2. The new pod starts. Its `StartupEvent` runs `recover()` with `active == null`. It finds the old pod's open run, ends it as `ABORTED_RESTART` and restores fixture stock.
  3. The old pod is still running and keeps executing the scenario until the new pod is Ready and the old pod gets SIGTERM. During that window it can place orders, for example in `inventory-contention`, after the reset. Its further `note()` calls also write audit rows after the `RESULT`/`RESET` rows.
- Result: fixture stock is left dirty after a "successful" reset, and the audit trail is confusing. A new run started on the new pod can briefly overlap the old pod's thread. Scaling to 2 replicas has the same effect: each pod aborts the other's runs.
- Suggested fix:
  - Set `strategy: Recreate` in the GitOps Deployment, matching `postgres.yaml`.
  - Document that the controller must run as a single replica.
  - Optionally record an owner (pod name) plus a heartbeat on `scenario_run`, and have recovery abort only runs whose heartbeat is stale.

### OPS-2 (Medium): stop, TTL halt or shutdown during an upstream call records `FAILED` and loses the guided reset step

- Code: `Engine.java:238-251` (`catch RuntimeException` → `failed`), `:258-273` (`halt` interrupts the thread, then waits) and `:225-228` (`shutdownNow`). `upstream/Http.java:71-73` turns an interrupt into `UpstreamException`.
- Failure scenario:
  1. An operator stops a run while the run thread is inside a call that is not wrapped in `await`, such as `orders.place`, `requireStock` or the setup `restore` in `InventoryContention`.
  2. The interrupt surfaces as `UpstreamException("… was interrupted")`. `execute()` records `FAILED` and calls `finish(..., guidedReset=null)` first.
  3. `halt`'s own `finish(STOPPED, guided step)` then becomes a no-op, because the first ending wins.
- Result:
  - The run shows `FAILED` instead of `STOPPED`/`EXPIRED`.
  - `scenario_runs_total{outcome="FAILED"}` is inflated.
  - For ERP scenarios the reset is `RESET_OK` instead of `RESET_GUIDED`, so the operator is not told to undo the console step.
- The same thing happens on pod shutdown through `shutdownNow()`: the run is ended `FAILED` and reset during shutdown, not `ABORTED_RESTART` as documented.
- Suggested fix: in `execute()`, treat any exception as "stopped" (`result = null`) when `handle.stop().get()` is true. Also add a test that stops a run during a slow `place`.

### OPS-3 (Medium-Low): a run whose scenario is no longer in the catalog blocks startup

- Code: `Engine.java:260` (`catalog.find(run.scenario()).orElseThrow()`) and `:205` (`recover` catches only `StoreException`).
- Failure scenario:
  1. A release renames or removes a catalog entry while a run of it is open, or a run was left open by a crash.
  2. `onStart` → `recover` → `halt` throws `NoSuchElementException` out of the `StartupEvent` observer.
  3. Startup fails and the pod crash-loops. The `RollingUpdate` keeps the old pod, but the rollout never completes. With `Recreate` the service would be down.
- The sweep has the same failure on every tick.
- Suggested fix: handle a missing catalog entry by ending the run `ABORTED_RESTART` with `RESET_FAILED` ("scenario no longer in catalog; restore by hand"). Also make `recover` catch `RuntimeException` and log, so recovery can never block startup.

### OPS-4 (Low): the claimed trace propagation is not established for run calls

- Code: `upstream/Http.java:109-115` uses `Span.current()`. The run executes on a plain `Executors.newSingleThreadExecutor` (`Engine.java:62, 124-127`) with no OpenTelemetry context.
- Docs: `docs/architecture.md:17` says "Every call carries … W3C `traceparent`".
- Failure scenario: almost every upstream call happens on the run thread. There is no current span there, so `traceparent` is omitted and run log lines carry no `traceId`. Only seeding and reset calls without a run (request thread) propagate a trace. Traces are also not exported (`application.properties:63`, `exporter=none`). That setting is platform-wide (asset-service, operations-console and order-service match), so it is not a defect of this change.
- Suggested fix: when a run starts, open a `scenario-run` span (or capture `Context.current()`) and run the task under `Context.wrap(...)`. Alternatively, correct the doc to say that correlation is by `X-Correlation-Id: scenario-<runId>`, with `traceparent` only when a span is active.

### OPS-5 (Low): some run log lines are missing the MDC fields, and the gauge can stick at 1

- Code: `Engine.java:245-252`.
- MDC: `scenarioRunId`/`correlationId` are removed in `finally` before `finish()`. The "Scenario ended" line and the reset upstream calls therefore log without them; the run ID appears only in the message text. Request-thread logs (start, stop, halt, recover) never set MDC.
- Gauge: if `finish()` throws (audit store down), `active = null` never runs. `scenario_active_runs` then reads 1 until the sweep ends the run at TTL+30 s.
- Suggested fix: remove MDC after `finish`, and clear `active` in a `finally`. Optionally put MDC in `halt`/`recover` as well.

### OPS-6 (Low): the configurable retention conflicts with the hard-coded 90-day trigger

- Code: `application.properties:46` (`SCENARIO_AUDIT_RETENTION`, default `P90D`), `RunStore.java:150-155` and `V1__scenario_schema.sql:45`.
- Failure scenario: setting retention below 90 days makes the trigger raise inside the nightly `DELETE`. The whole statement aborts and nothing is purged, every night, with only a scheduler error in the log. The cutoff also uses the application clock while the trigger uses the database `now()`. On a single node this is practically identical, but if the database clock lags, a boundary row aborts the batch.
- Suggested fix: remove the knob, or validate at startup that it is at least `P90D`. Compute the cutoff in SQL (`now() - interval`).

### OPS-7 (Low): runbook recovery steps don't match the code in two places

Location: `docs/runbook.md:35-37` and `docs/architecture.md:31-32`.

1. "If the pod cannot start, the run still ends at its TTL once the pod is back (sweep)" is wrong. On start, the run is ended immediately as `ABORTED_RESTART` (`Engine.onStart`), not at TTL.
2. "If the database is down at startup, the sweep retries" cannot happen. `quarkus.flyway.migrate-at-start=true` fails startup when the database is down, so the pod crash-loops and the `recoveryPending` retry path is unreachable in prod.

In addition, the only manual recovery offered (`scenario.sh reset`) needs a working controller. The requirement asks for documented manual recovery after a crash mid-scenario. When the controller cannot start, the runbook should give an out-of-band step: restock fixture records through inventory's `restock` API with the inventory-admin identity, and the ERP console undo steps.

Suggested fix: correct both statements and add the out-of-band procedure.

### OPS-8 (Low): no backup/restore or migration rollback guidance for the audit store

Location: `docs/runbook.md` (missing section).

Quality gate 03 requires "migration rollback and backup/restore instructions for stateful changes". This change adds a PostgreSQL audit trail with append-only triggers, and nothing documents how to back it up (`pg_dump` from the `scenario-controller-postgres` pod or the PVC) or how to roll V1 back.

Suggested fix: add a short section to the runbook.

### OPS-9 (Low): the GitOps Deployment still needs the run19 configuration

Location: `deployment.yaml:41-47` and `kustomization.yaml:18-29`.

Today the Deployment only provides the ConfigMap and the Postgres Secret (`QUARKUS_DATASOURCE_*` is present). Deploying `e061f6d` as-is starts and passes smoke, but every action is refused. That is fail-closed and correct.

To make it usable, the GitOps PR must add `env:` entries in the Deployment, following the asset-service pattern and the box1-docs#42 lesson:

- `POD_NAMESPACE` from `fieldRef: metadata.namespace`
- `SCENARIO_CONTROL_ENABLED`
- `SCENARIO_NAMESPACE_ALLOWLIST` (the namespace the user names)
- `SCENARIO_ENVIRONMENT=dev`
- `INVENTORY_TOKEN_URL` and `INVENTORY_TOKEN_CLIENT_ID`
- `INVENTORY_TOKEN_CLIENT_SECRET` through `secretKeyRef`, never the ConfigMap
- optionally the explicit `ORDER_SERVICE_URL`, `INVENTORY_SERVICE_URL` and `FULFILLMENT_ADAPTER_URL`
- optionally `-XX:+ExitOnOutOfMemoryError`

Add `strategy: Recreate` (OPS-1) in the same PR.

Fail-closed check:

- Control defaults to `false`, the namespace to "unknown" (refused), and the allowlist to empty (refused).
- The inventory token defaults to `none`, so seeding and reset report "not configured".
- `SCENARIO_ENVIRONMENT` defaults to `unknown`, which only affects labeling.
- The upstream URL defaults (`application.properties:40-42`) point at the dev services. In another environment where the gates are opened but the URLs are not set, the controller would drive dev services. Suggested fix: no defaults in `%prod`, or document this.

`KAFKA_BOOTSTRAP_SERVERS` (`kustomization.yaml:29`) is harmless. The Kafka extension and every `mp.messaging` key are gone, so nothing reads it. Remove it in the same PR for clarity, since the README says Kafka is not used.

### OPS-10 (Info): the README is stale after this change

- `README.md:101`: "no external dependency CVE database scan is implied". Release now runs `box1-security-gates` with `enforcement: gate` (RHTPA/RHACS).
- `README.md:95`: "runtime has no API token". This stops being true once the inventory client secret is configured.
- The runbook's configuration table omits these tunables: `SCENARIO_AUDIT_RETENTION`, `SCENARIO_UPSTREAM_TIMEOUT`, `SCENARIO_POLL_INTERVAL`, `SCENARIO_EXPIRY_INTERVAL`, `SCENARIO_MINIMUM_VISIBLE_DELAY`, `SCENARIO_JWT_ISSUER`, `SCENARIO_JWKS_URL` and `PUBLIC_API_URL`.

### OPS-11 (Info): the reset outcome is not measurable

`RESET_FAILED` is recorded only in the database and the log. There is no `scenario_resets_total{result}` counter, so a reset failure (for example, the inventory identity missing) cannot be alerted on.

Separately, the counters are created on first use, so they are absent until the first run or refusal. Also, nothing in the platform scrapes `/q/metrics`: there are no scrape annotations or ServiceMonitor in any workload. That gap is platform-wide.

### OPS-12 (Info): `scripts/scenario.sh` puts the bearer token in curl's argv

Location: `scripts/scenario.sh:12`.

The token is visible to other local users through `ps` while curl runs. For the security pass: consider `-H @-` or a `--config` file read from stdin.

## Areas checked with no finding

- **Readiness and liveness:** readiness is the audit store only (`DatabaseReadinessCheck`, `isValid(2)`). Upstreams are not checks; their failures are reported per run. Liveness is constant. The probe timeouts (2 s) and the startup budget (150 s) are adequate. Startup recovery calls inventory, but restore stops at the first failure, so startup is bounded at about 10 s.
- **Resources:** 100m/256Mi requests, 512Mi limit, `MaxRAMPercentage=50`. The template build uses 143Mi live and Postgres 31Mi. These fit the single node. `e061f6d` was not measured because it is not deployed.
- **Scheduler:** the sweep runs every 5 s with `SKIP`. It ends runs past TTL+30 s, including runs with no thread (an insert followed by a failed audit or submit). Concurrent `onStart` and sweep recovery are safe: `finish` is synchronized and the first `end` wins. The retention cron is `0 17 3 * * ?` UTC with `SKIP`. Audit rows are purged first, then ended runs without audit rows, which respects the foreign key.
- **One-run invariant:** the partial unique index serializes starts across threads and pods. The in-memory `active` handle is the only per-pod state (see OPS-1).
- **Metric cardinality:** the tags are `scenario` (from the catalog only; unknown names are never tags), `outcome` (an enum) and `action` (fixed verbs). This is bounded. `scenario_active_runs` is registered once on the CDI instance and is strongly held.
- **JSON logs:** prod uses JSON (`quarkus-logging-json`, disabled only in dev and test) with `service.name`. The run thread carries `scenarioRunId` and `correlationId` in MDC (see OPS-5 for gaps). Upstream errors are logged without bodies, and the token is never logged.
- **Smoke compatibility:** `/api/greetings` and `/api/info` are unchanged and anonymous. `/q/health/*` and `/q/openapi` are anonymous, and the OpenAPI document still lists `/api/greetings` and `/api/info`. `/q/metrics` is anonymous and `box1_greetings_total` is still emitted by `GreetingResource`. `/q/health/ready` needs the audit database, which GitOps provides. Proactive auth is off, and the JWKS is fetched only on the first authenticated call.
- **Network:** the Postgres NetworkPolicy admits `app.kubernetes.io/name=scenario-controller`. The upstream namespaces have no ingress policy on their application pods (only on their databases), so the controller can reach them.
- **Kafka removal:** `quarkus-messaging-kafka` and the `mp.messaging` properties are removed, so `KAFKA_BOOTSTRAP_SERVERS` is inert (OPS-9).
- **Release gates:** `.tekton/release.yaml` now uses `security-gates: gate`, consistent with asset-service, operations-console, order-service and fulfillment-adapter. The Guava `33.7.2-jre` override in `dependencyManagement` matches those repositories and resolves locally (`~/.m2`). It has no backlog link for removal; the same is true of its peers.
- **Shutdown and restart semantics (apart from OPS-1 and OPS-2):** a run never resumes silently. A run left open is aborted and reset at the next start. `terminationGracePeriodSeconds: 30` exceeds `halt`'s 10 s wait.
