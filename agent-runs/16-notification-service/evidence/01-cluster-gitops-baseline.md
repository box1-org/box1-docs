# Phase 0 GitOps and cluster baseline

Observed 2026-11-05 23:34–23:37 EST (America/New_York). Read-only: `git show` against fetched `origin/main`, `oc get`, and `gh`. No Secret values were read.

## Revisions

| Repository | origin/main |
|---|---|
| box1-workloads-dev | `7b5813d` |
| box1-gitops | `5e05888` |
| box1-templates | `badc3c3` |
| box1-ops-contracts | `d57a4ef` |
| notification-service | `3db3fbc` (template scaffold, template 1.1.0) |

## notification-service onboarding (box1-workloads-dev)

- Onboarded by box1-workloads-dev#91 (merged 04:30:09Z) and the promotion PR #92 (merged 04:32:22Z, 2026-11-06 UTC).
- `applications/notification-service.yaml`: automated, `selfHeal: true`, **no prune**, `PruneLast=true`, destination `notification-service-dev`.
- `workloads/notification-service/`: namespace (`pod-security enforce: restricted`), serviceaccount, deployment, service, route (`notification-service-dev.apps.ocp.box1.org`, edge, Redirect), onboarding (PaC Repository, image puller, release observer).
- **`postgres.yaml` is empty (1 byte) and not in the kustomization.** The service was onboarded with PostgreSQL off. No database Secret is committed for this service.
- ConfigMap literals: `GREETING_PREFIX`, `JAVA_TOOL_OPTIONS`, `KAFKA_BOOTSTRAP_SERVERS=box1-kafka-kafka-bootstrap.box1-kafka.svc:9092`.
- Deployment: requests 100m/256Mi, limits 1 CPU/512Mi; probes `/q/health/{started,ready,live}`; read-only root FS; no `env:` block (no `POD_NAMESPACE`, datasource or OIDC settings). No NetworkPolicy.
- Image `box1-ci/notification-service@sha256:abc6446a1092eb5a0eedbc816c66612827f49b063cd0949e6d2e98525264b582`, from PipelineRun `onb-notification-service-3db3fbcb` (Succeeded). No release or smoke run yet.

Pattern for comparison: asset-service adds PostgreSQL with **no Secret in Git** (the user creates `asset-service-postgres` out of band), puts post-onboarding settings in Deployment `env:` rather than the hashed ConfigMap (#42), and passes `POD_NAMESPACE` from the downward API for its chaos allowlist.

## Argo CD (23:35 EST)

| Application | Sync | Health | Revision |
|---|---|---|---|
| notification-service | Synced | Healthy | 7b5813d |
| box1-workloads-dev | Synced | Healthy | cd5653f |
| box1-kafka | Synced | Healthy | 5e05888 (manual sync only) |
| keycloak | Synced | Healthy | 5e05888 (automated, selfHeal, `prune: false`) |

## Kafka

- `box1-kafka` (Strimzi 0.51 / AMQ Streams 3.2.2), Kafka 4.2.0, KRaft, RF 1.
- One listener: `plain` 9092, internal, no TLS. No KafkaUsers or ACLs.
- `box1.notification.events.v1`: 3 partitions, 14 d, Ready.
- DLQ topics exist for order, inventory, fulfillment and telemetry (3 partitions, 14 d). **No notification DLQ topic** in Git or on the cluster.

## Keycloak (realm `box1`, RH-SSO 7.6 operator)

- KeycloakClients on the cluster, all ready: `asset-service`, `developer-hub`, `fulfillment-adapter`, `openshell-cli`. **No notification client.**
- `operations-console` exists only in open PR box1-gitops#73 (#18 run D-002): public PKCE client, `fullScopeAllowed: false`, roles `console-viewer`, `console-operator`, `console-developer`, audience mappers for itself, `inventory-service` and `fulfillment-adapter`. The console backend forwards the signed-in user's access token.
- asset-service pins `azp=asset-service`; fulfillment-adapter checks `aud` only.
- #59 is closed as not a defect: the operator did create the client roles, on a later reconcile.

## Release smoke (`box1-quarkus-smoke`, box1-gitops `platform/pipelines/tasks/quarkus-smoke.yaml`)

Unauthenticated: `/api/greetings?name=OpenShift` (expects `Hello from box1, OpenShift!`), `/api/greetings?name=%20` → 400, `/api/info` (javaVersion 21, name, gitRef), `/q/health/{live,ready,started}`, `/q/openapi` containing `/api/greetings` and `/api/info`, `/q/metrics` containing `box1_greetings_total`.

## Node `quark.host.box1.org`

Allocatable 31.5 CPU / ~124.6 GiB. Requested 21.75 CPU (69%) / ~84 GiB (67%). Limits overcommitted (256% CPU, 149% memory).
