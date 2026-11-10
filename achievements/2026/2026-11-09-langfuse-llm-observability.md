# Langfuse: self-hosted LLM observability with Keycloak sign-in

**Date:** 2026-11-09 (America/New_York). The issue was filed at 22:07 EST, the last merge was at 23:00 EST, and the final check was at 23:05 EST. Cluster and GitHub timestamps below are UTC (EST + 5 h).

**Status:** Delivered and live. Seven of the eight acceptance criteria in [box1-docs#155](https://github.com/box1-org/box1-docs/issues/155) were met before this log; the eighth is this log. No temporary workaround is in place.

## Outcome

Langfuse 4.77.0 runs on the cluster at <https://langfuse.apps.ocp.box1.org>. Box1 now has somewhere to send and inspect LLM traces, generations, prompts and evaluations, for example from the agentic-operations assistant, Developer Lightspeed experiments or new AI services.

- People sign in with Keycloak (realm `box1`). Their first sign-in places them in org `box1` as Viewer.
- A local owner account handles administration and break-glass.
- Local self-signup is closed.
- Applications send traces with project API keys over OpenTelemetry.

Everything is managed by Argo CD from `box1-gitops`. No credential is stored in Git.

| Item | Value |
|---|---|
| Argo CD Application | `langfuse` (`applications/langfuse.yaml` → `platform/langfuse`), automated sync with prune, self-heal and retry |
| Namespace | `langfuse`, Pod Security `restricted`; all pods run under an OpenShift-assigned UID (`restricted-v2`) |
| Web / worker | `langfuse/langfuse` and `langfuse/langfuse-worker` 4.77.0, pinned by digest, 1 replica each |
| PostgreSQL | `registry.redhat.io/rhel9/postgresql-15` (OpenShift catalog), 10 GiB PVC |
| ClickHouse | `clickhouse/clickhouse-server` 26.3.62.3, single node (`CLICKHOUSE_CLUSTER_ENABLED=false`), 20 GiB PVC. This is the version Langfuse's 4.77.0 reference compose file uses |
| Redis | `registry.redhat.io/rhel9/redis-7` (OpenShift catalog), `maxmemory-policy noeviction`, AOF on, 2 GiB PVC |
| S3 | NooBaa ObjectBucketClaim `langfuse-bucket` (prefixes `events/` and `media/`). In-cluster endpoint `s3.openshift-storage.svc`, trusted through the injected service CA |
| Sign-in | Keycloak confidential client `langfuse` (authorization code + PKCE), plus the local owner `langfuse-admin@box1.local` |
| Exposure | Edge Route with the cluster's Let's Encrypt wildcard certificate. Ingress NetworkPolicies are default-deny: only the router reaches web, and only web and worker reach the datastores |
| Runbook | [`platform/langfuse/README.md`](https://github.com/box1-org/box1-gitops/blob/main/platform/langfuse/README.md) |

## Starting baseline

These are read-only observations from 2026-11-09, before any change:

- **Cluster:** single node `quark.host.box1.org`, OpenShift 5.0.0-rc.7 (Kubernetes 1.36.5), 32 CPU and 128 GiB.
- **Node load:** requests were at 68% CPU and 78% memory; actual use was 24% CPU and 72% memory.
- **Storage:** `lvms-vg1` (default, `WaitForFirstConsumer`) and NooBaa (`openshift-storage.noobaa.io`, one `pv-pool` backing store, Ready).
- **Existing tools:** no Langfuse or other LLM-observability tool existed in the cluster or in box1-org, and no backlog item covered one.
- **Identity:** Keycloak (RH-SSO 7.6, realm `box1`) already served twelve clients through `KeycloakClient` CRs.
- **Versions:** the current Langfuse release was 4.77.0, a major version newer than the 3.x most public guides describe. Its v4 requirements were taken from the release's own `docker-compose.yml`, entrypoints and source, not from earlier knowledge.

## What changed

| Change | Merge (UTC) | Content |
|---|---|---|
| [box1-docs#155](https://github.com/box1-org/box1-docs/issues/155) | filed 03:07 | Design, decisions and acceptance criteria |
| [box1-gitops#142](https://github.com/box1-org/box1-gitops/pull/142) | `2c799b5`, 03:13 | Adds `platform/langfuse`, the `langfuse` Application, Keycloak client `platform/identity/keycloak/realm/langfuse-client.yaml`, and a README |
| [box1-gitops#144](https://github.com/box1-org/box1-gitops/pull/144) | `423f47b`, 03:21 | Moves the three PVCs into their Deployments' sync wave (see *Incidents*) |
| [box1-gitops#145](https://github.com/box1-org/box1-gitops/pull/145) | `2ac4a69`, 04:00 | Closes `/api/auth/signup-verify` with a second Route and drops two no-op settings. README corrections: OTLP-only ingestion, and the worker startup race |

**Design decisions:**

- **Kustomize manifests, not the upstream Helm chart.** The chart's Bitnami subcharts don't fit the repository's conventions: digest-pinned images, Red Hat catalog images where available, and the `restricted` SCC. Plain manifests follow the existing `mailhog` and `keycloak` pattern.
- **Sign-in model, chosen by the user:** Keycloak SSO for everyone, plus one headless-initialised local owner.
  - Only the owner may create organisations (`LANGFUSE_ALLOWED_ORGANIZATION_CREATORS`).
  - New SSO users get org role Viewer (`LANGFUSE_DEFAULT_ORG_ID/ROLE`).
- **Self-signup is closed at the Route, not in Langfuse.** Langfuse's `AUTH_DISABLE_SIGNUP` also throws in the NextAuth adapter's `createUser`, which would refuse first-time SSO users (checked in v4.77.0 `web/src/server/auth.ts`). Instead, two path Routes send `/api/auth/signup` and `/api/auth/signup-verify` to a Service with no endpoints, so both return 503.
- **No secrets in Git.** An Argo CD Sync-hook Job, `langfuse-bootstrap`, does two things:
  - It generates `langfuse-secrets` once and never overwrites it. The values are hex passwords, so they need no URL encoding in the database connection URLs.
  - It copies the RH-SSO operator's `keycloak-client-secret-langfuse` into `langfuse-keycloak`. A Role in `keycloak` lets it read only that Secret.

  Web and worker read the S3 credentials directly from NooBaa's `langfuse-bucket` Secret and ConfigMap.
- **Telemetry to Langfuse is off** (`TELEMETRY_ENABLED=false`).

**Made outside Git:**

- **Applied by hand before #142 merged:** the `langfuse` Namespace and the `langfuse` KeycloakClient. Both were identical to the PR, and Argo CD adopted them on its first sync. Applying the rest by hand was blocked by the session's permission check, so everything else arrived through Argo CD.
- **Merges:** the user merged all three PRs.
- **Refreshes:** I triggered Argo CD refreshes by annotating `box1-root`, `keycloak` and `langfuse`.
- **Stuck sync:** I terminated the first `langfuse` sync operation by setting its phase to `Terminating` (see below).
- **Worker restart:** I deleted one worker pod.

## Incidents during rollout

**1. The first sync stalled in wave -1.**
- **Symptom:** Argo CD reported `waiting for healthy state of /PersistentVolumeClaim/langfuse-clickhouse-data and 2 more resources`. The PVCs were Pending, the bootstrap Job (wave 0) had not started, and no pods existed.
- **Cause:** `lvms-vg1` binds a volume only when a pod mounts it, but the PVCs were in wave -1 and their Deployments in wave 1.
- **Fix:** #144 put each PVC in its Deployment's wave, as Keycloak's database already does. The stuck operation was then terminated, and the next sync completed at `423f47b` within about 2 minutes.

**2. The worker raced the ClickHouse migrations on first start.**
- **Symptom:** the worker logged `Table default.events_full does not exist`, then `Failed to detect ClickHouse event-size DEFAULT; using legacy estimates`.
- **Cause:** the worker started while web was still applying the migrations. It checks the table only at startup, and data was not affected.
- **Fix:** the worker pod was deleted after web was Ready, and the new pod started without errors. This can recur on a first install or an upgrade that adds ClickHouse migrations, so it is documented in the README.

**3. Signup-verify was not covered by the signup Route.**
- **Symptom:** after #142, `POST /api/auth/signup` returned 503, but `/api/auth/signup-verify` reached Langfuse, which answered 404 "Email verification signup is not enabled."
- **Cause:** the OpenShift router matches a Route path by whole segments, not as a string prefix.
- **Exposure:** that endpoint acts only when `AUTH_EMAIL_VERIFICATION_REQUIRED=true` and SMTP are both set (`credentialsUtils.ts`), and neither is. So signup was not open.
- **Fix:** #145 added a second Route so that configuring mail later cannot open signup, and corrected the docs that had claimed both paths were covered.

## Validation and evidence

All checks ran against the live deployment through the public Route unless stated otherwise. The full record is in the [#155 comments](https://github.com/box1-org/box1-docs/issues/155).

| Check | Expected | Result |
|---|---|---|
| Argo CD | Synced / Healthy from `main` | Synced / Healthy at `2ac4a69`, and later at `5365f0d`, an unrelated commit |
| Pods | All Running under `restricted-v2` | 5 pods Running with 0 restarts, all under UID `1001080000` |
| Bootstrap | Secrets created, nothing in Git | Job Complete. `langfuse-secrets` has 9 keys and `langfuse-keycloak` 2. The PVCs and OBC are Bound |
| Migrations | PostgreSQL and ClickHouse applied | 470 Prisma migrations applied. ClickHouse at schema version 56, not dirty, `events_full` present |
| Redis | `noeviction`, persistent | `maxmemory-policy noeviction`, `appendonly yes` |
| TLS | Trusted certificate, HTTPS only | Let's Encrypt `*.apps.ocp.box1.org` (expires 2027-01-21). HTTP → 302 |
| Health | OK | `/api/public/health` and `/ready`: `{"status":"OK","version":"4.77.0"}` |
| Keycloak SSO | Realm user signs in and lands in `box1` as Viewer | The user signed in at 03:26 UTC: a `keycloak` OAuth account linked to an SSO-only user, org role **VIEWER**. No auth errors in the web logs |
| Local owner | Can sign in | The account exists in PostgreSQL as **OWNER** of `box1`. The user reported a successful sign-in; I did not sign in with the password myself |
| Self-signup refused | 503 | `POST /api/auth/signup`, `POST` and `GET /api/auth/signup-verify`, and `POST /api/auth/signup/x`: all **503** after #145 |
| Unauthenticated API | 401 | `/api/public/projects` with no auth, and `/api/public/ingestion` and `/api/public/otel/v1/traces` with no or bogus keys: all **401** |
| End-to-end ingestion | Trace stored and readable | An OTLP/JSON root span plus generation, sent with the initial project's keys, returned 200 (details below) |
| After the #145 restart | No regression | Sign-in page 200, both providers, health OK, 401s unchanged. A second OTLP trace was read back with SPAN + GENERATION |

The end-to-end ingestion test followed one trace through the whole pipeline:
1. Web wrote the payload to the bucket at `events/otel/box1-default/2026/11/10/03/27/…json` (object listed with S3 SigV4).
2. Web queued `otel-ingestion-job` in Redis.
3. The worker wrote both observations to ClickHouse `events_full` (`GENERATION fake-llm-call`, `SPAN box1-deploy-verification`).
4. Both were read back through `/api/public/v2/observations?traceId=…`.

Resource use at 04:05 UTC with no load was about 0.17 CPU and 2.1 GiB. Requests are about 0.7 CPU and 2.9 GiB; limits are 9.5 GiB.

**Not tested or not established:**

- **Media uploads:** an SDK media upload through the presigned public S3 route (`s3-openshift-storage.apps.ocp.box1.org`), and whether NooBaa needs bucket CORS for browser uploads.
- **Other features:** evaluations, LLM connections and prompt management.
- **Load:** behavior under load, and ClickHouse memory growth over time.
- **Backup and restore:** none was configured or exercised.
- **Other users:** a non-owner raising another user's role, and SSO for a realm user without an email address. That user is expected to fail, since Langfuse requires the email claim.
- **Vendor support:** whether Langfuse or ClickHouse support this OpenShift version is not established. Langfuse is community-supported self-hosting here.

## Final operational state

- **Management:** Argo CD Application `langfuse` runs from `box1-gitops` `main` with automated sync, prune and self-heal. The last change to the Langfuse paths is `2ac4a69`. There is no manual override, and the live state matches Git.
- **Keycloak client:** managed by the `keycloak` Application.
- **Secrets:** the two Secrets the Job creates (`langfuse-secrets`, `langfuse-keycloak`) are deliberately outside Argo CD's management, so it never prunes them. They are listed in [`manual/manual-installs-and-secrets.md`](../../manual/manual-installs-and-secrets.md).
- **Data in Langfuse:** org `box1`, project `box1-default`, 2 users (the owner and one SSO Viewer), 1 API key (the initial project key), and the two verification traces.
- **Ingestion API change in v4:** Langfuse 4 accepts traces only over OpenTelemetry. The legacy `/api/public/ingestion` takes score events only and returns HTTP 400 for `trace-create`, and `/api/public/traces/{id}` returns 404. Clients must use current Langfuse SDKs or an OTLP exporter.
- **Project roles:** per-project roles need Langfuse's enterprise `rbac-project-roles` entitlement. Without it, the org role applies to every project.

## Recovery and follow-ups

- **Credentials to preserve:** `langfuse-secrets` must be kept with the PVCs.
  - `SALT` hashes the stored API keys.
  - `ENCRYPTION_KEY` encrypts stored LLM-connection keys.
  - The database passwords are baked into the initialised data.

  Deleting it while keeping the data locks Langfuse out of that data. Back it up outside Git.
- **Removal:** delete `applications/langfuse.yaml`. Argo CD prunes the workloads, but the PostgreSQL and ClickHouse PVCs, the bucket claim and the two Secrets remain (`Prune=false,Delete=false`, or not Argo-managed) until deleted by hand. Remove `langfuse-client.yaml` from the realm separately.
- **Rollback of the fixes:** reverting #145 would reopen the documentation error and leave `/api/auth/signup-verify` reachable. Reverting #144 would bring back the sync deadlock on any re-create. Neither rollback was exercised.
- **Not filed:** backups for the Langfuse PostgreSQL and ClickHouse data, and tests of media upload and evaluations. Both wait on the user's decision. Box1 has no general backup mechanism yet.
- **Related:** NooBaa's single `pv-pool` backing store limits availability. While it is down, Langfuse cannot store events ([box1-docs#43](https://github.com/box1-org/box1-docs/issues/43)).
