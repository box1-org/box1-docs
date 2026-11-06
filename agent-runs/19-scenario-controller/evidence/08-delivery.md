# Phase 6 delivery, 2026-11-06 (EST)

The user's approvals, 2026-11-06 about 12:50 EST: A-1 merged by the user; A-2 "authorized" (open the contracts PR); A-3 and A-4 "do it yourself"; A-5 "authorized"; A-6 "do it"; O-13 "open up a ticket". Not approved: A-7 (role assignment), A-8 (seeding), A-9 to A-11 (live runs), O-11 and O-14.

Clocks: host 12:50:38 EST at the start; there were no sleep gaps during delivery.

## Merges and releases

| Step | Result | Evidence |
|---|---|---|
| A-1 inventory-service#3 | Merged by the user as `ad472e1`, 12:48 EST. Release `inventory-service-release-fblwj` Succeeded; promotion box1-workloads-dev#106 merged automatically. The deployment in `inventory-service-dev` runs `sha256:c8b33f7a…7601b`, which matches the release's `image-digest` result. Logs: "Successfully applied 1 migration" (V3) | `oc get pipelinerun`, `oc get deploy`, pod logs |
| A-2 contract | box1-ops-contracts#10 opened (branch `run19-inventory-fixture-routes`), adding the two routes. `npm run validate` passes (10 event fixtures, 11 schemas, 20 OpenAPI examples); `npm test` passes 76/76. **Not merged**; merging needs approval | PR #10 |
| A-3 scenario-controller#1 | Merged as `f64dee6`, 12:51 EST. Release `scenario-controller-release-v9qm4`: build, security (gate mode; scan critical 0, high 10, medium 158, low 83), promote and smoke all Succeeded. Image `sha256:a811c457…b269`. Promotion box1-workloads-dev#107 merged automatically (`bd24fe1`) | PipelineRun results |
| A-4 box1-gitops#78 | Merged as `7d7e0b1`. Argo `keycloak` (automated, selfHeal, prune off) refreshed: Synced, Healthy, operation Succeeded at `7d7e0b1`. KeycloakClients `inventory-service`, `scenario-controller` and `scenario-controller-cli` created. Operator log: roles `inventory-admin`, `scenario-viewer` and `scenario-operator` created (SUCCESS). **Failure:** both scope mappings fail with `(404) 404 Not Found`, so `scenario-controller` and `scenario-controller-cli` report `ready=false`, and the service-account role step is not reached. Repair 14 below | operator log, `oc get keycloakclient` |
| A-5 Secret | `scenario-controller-inventory-token` created in `scenario-controller-dev`, key `client-secret`, copied by a pipe from `keycloak-client-secret-scenario-controller` (key `CLIENT_SECRET`). The value was never printed or stored; only the key names and the encoded length were checked. Labelled `box1.org/source=keycloak-client-secret-scenario-controller`. It is not in Git, so Argo does not manage it | `oc get secret` (metadata) |
| A-6 box1-workloads-dev#103 | Trial merge against main showed no conflict. Merged as `e28c020`. Argo `scenario-controller` Synced and Healthy at `e28c020`; rollout complete; strategy `Recreate`; image `sha256:a811c457…b269` | `oc rollout status`, Argo status |

## Deployed controller: read-only checks

Route: `scenario-controller-dev.apps.ocp.box1.org`.

| Check | Expected | Observed |
|---|---|---|
| `GET /q/health/ready` | 200 UP | 200, `UP`, check `database` UP |
| `GET /internal/v1/scenarios` without a token | 401 | 401 |
| `GET /internal/v1/runs`, `/internal/v1/audit` without a token | 401 | 401, 401 |
| `GET /internal/v1/scenarios` with a malformed bearer token | 401 | 401 |
| `GET /q/openapi` | 200 | 200 |
| Flyway | V1 and V2 | "Successfully validated 2 migrations … Current version of schema public: 2 … up to date". The template had no migrations |
| Startup log WARN/ERROR | none | none (the only match is the JVM options notice) |

**Not tested:**
- An authorized catalog read: no one holds a `scenario-*` role yet (A-7), and the CLI client is not ready (repair 14).
- The gate state as seen by an operator.
- Seeding, and every scenario run.

## Repair 14: scope mappings need the target client's internal ID

**Symptom.** The operator logs `FAILED create client client scope mappings keycloak/scenario-controller => inventory-service: (404)`, and the same for `scenario-controller-cli => scenario-controller`.

**Cause.** The scope-mapping endpoint is `/clients/{id}/scope-mappings/clients/{targetId}`, and it takes the target client's internal UUID. #78 set only `client:` (the clientId), so the operator sent an empty ID.

**Local reproduction.** On the run's Keycloak 26.4: with the clientId the call returns 404; with the UUID it returns 204.

**Fix.** box1-gitops#79 (branch `run19-keycloak-scope-mapping-ids`, PR checks pending at filing) pins `spec.client.id` on `inventory-service` and `scenario-controller` to the UUIDs Keycloak already generated, so the live state doesn't change, and sets `id` on each `clientMappings` entry. `oc kustomize` passes, and `oc create --dry-run=client --validate=strict` accepts all three files.

**Status.** It needs a merge approval and the Argo sync. Until then, the controller's service account lacks `inventory-admin`, so seeding would get 403, and the CLI client is not ready.

**Lesson.** In #59 and Phase 0 I checked that the operator creates roles; I didn't check client scope mappings, because nothing else in box1-gitops used them. An unused CR feature needs its own local proof before the merge.

## Follow-up ticket (O-13)

box1-docs#72 records three follow-ups with acceptance criteria: an ERP-side expiry for demo faults and holds, a fixture-only inventory role, and rate-limited audit of refused requests.

## Side effects of this phase

- Secret `scenario-controller-inventory-token` (above).
- Argo refresh annotations on the `keycloak` and `scenario-controller` applications.
- One unneeded `oc exec … psql -c "select 1"` in `scenario-controller-postgres`. It was a read, its output was discarded, and no credential was used or shown. It was not necessary and is recorded here.
