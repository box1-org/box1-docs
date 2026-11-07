# Onboarding baseline

Observed 2026-11-06 22:32–22:40 EST. The user onboarded the service in Developer Hub (Q-1), using template `quarkus-rest-service` with Kafka on and PostgreSQL off.

| Item | Value |
|---|---|
| Repository | `box1-org/agentic-operations` (public), created 2026-11-07T03:30:18Z |
| Scaffold | `61bcb8c` "Create Quarkus service from the Box1 golden path" (Quarkus 3.40.1.1, Java 21, `quarkus-messaging-kafka`, no datasource) |
| GitOps onboarding | box1-workloads-dev #146, merged 03:31:04Z (`fe383c6`) |
| First promotion | box1-workloads-dev #147, merged 03:33:26Z |
| Onboarding build | `onb-agentic-operations-61bcb8c3`, Succeeded |
| Argo | `agentic-operations` Synced/Healthy at `b108126` |
| Image | `box1-ci/agentic-operations@sha256:eb145100ffbb6a6bcb8d6f338d8ccfdcc135174ecf66aef31fb853da67f2dbd1`; the running pod's imageID matches |
| Endpoint | `GET https://agentic-operations-dev.apps.ocp.box1.org/api/info` → `gitRef 61bcb8c3…`; `/q/health/ready` → 200 |
| Workload files | deployment, kustomization, namespace, onboarding, postgres (not used), route, service, serviceaccount |

Observations for later phases:

- The scaffold's CORS allows every method for the Developer Hub origin. Phase 3 narrows this to what the API needs.
- `postgres.yaml` exists in the workload directory. Whether it is listed in the kustomization is checked at the runtime PR.
- Until promotion #147 synced, the Deployment pointed at an all-zero placeholder digest. That is expected onboarding behavior, observed for about 2 minutes.
