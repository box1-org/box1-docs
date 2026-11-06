# Release reviewer pass (Phase 6), 2026-11-06 ~13:20 EST

A fresh read-only subagent independently checked the delivery: merges, release results, Argo state, Deployment, the Secret's metadata, the env against `application.properties`, #79, and rollback. No Secret value was read. This is a same-model review.

**Confirmed:**
- every merge SHA and image digest in `evidence/08-delivery.md` matches the live state;
- Argo `scenario-controller` is Synced at `e28c020`, all 17 resources are Synced, and no generated ConfigMap was orphaned;
- 1 replica, Recreate, Flyway at version 2;
- the env matches the controller's settings (all three gates set, `allowed-azp=scenario-controller-cli`).

| # | Severity | Finding | Outcome |
|---|---|---|---|
| R-1 | High | Seeding is blocked until box1-gitops#79 merges: no scope mapping, and it is not established that the service account holds `inventory-admin` | **Known (repair 14).** After #79, check the client-credentials token's claims (aud `inventory-service`, role `inventory-admin`) before seeding |
| R-2 | Low | #79's UUIDs match the live values and the CRD schema has `clientMappings.*.id`. It holds only while Keycloak is rebuilt from these CRs. The 204/404 test was against Keycloak's API, not the operator | **Recorded.** #79 is not verified until both CRs report ready |
| R-3 | Medium | The `gate` security mode enforces RHACS build policies (`roxctl image check`), not vulnerability counts: 10 high passed with policy `pass` | **Corrected** in `evidence/08` and the pilot log: "gate passed" means no enforced ACS policy fired, not "no high vulnerabilities". inventory-service shows the same counts (shared base image) |
| R-4 | Medium | The controller's database Secret in the public workloads repository | **Already reported to the user directly (O-11, #41 pattern).** Pointer only |
| R-5 | Low | The hand-copied token Secret isn't in Git and goes stale silently if Keycloak rotates it | **Recorded** as a temporary workaround in box1-docs#72 (item 4) |
| R-6 | Low | The release smoke ran against the image-only rollout (#107), not the pod after #103's env change | **Covered:** `evidence/08`'s read-only checks (ready UP, 401s, OpenAPI) ran against the final pod after #103's rollout |
| R-7 | Info | Rollback: revert #107 (and #103) in box1-workloads-dev. That returns the scaffold image `175401a5…`, which ignores the V1/V2 tables. Self-heal undoes `oc rollout undo` | **Recorded** in handoff (untested) |
| R-8 | Info | No drift; the workloads main head moved for an unrelated legacy-erp change | No action |
