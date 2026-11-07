# D-014 Migration and rollout plan

**Status:** decided by the run. Every merge, sync, new Secret and cluster fault run is a separate user approval.

Order matters: the first release after merge must find its database, Secret, DLQ topic and Keycloak issuer, or the smoke gate fails.

1. **Contracts PR** (box1-ops-contracts): notification schemas + `TOPICS.md` group. Merge → approval. The service pins `contracts.ref` to the merged commit (or the PR head until then).
2. **Service PR** (notification-service, branch `issue-16-notification`): implementation, Flyway V1, tests, docs. PR CI runs the Golden Path validate pipeline. Not merged yet.
3. **Shared infrastructure PRs** (box1-gitops), each its own approval to merge and then to sync:
   - `platform/kafka/topics/notification-dlq.yaml` → selective `box1-kafka` sync of that resource, prune off;
   - `platform/identity/keycloak/realm/notification-service-client.yaml` → `keycloak` auto-sync; then check the two roles exist on the cluster.
4. **Secret** `notification-service-postgres`, created by the user out of band (approval; value never recorded).
5. **Workloads PR** (box1-workloads-dev): PostgreSQL + NetworkPolicy + Deployment `env` (`POD_NAMESPACE`, datasource, OIDC issuer/JWKS, `NOTIFY_EVENTS_FLOOR`, faults disabled, empty allowlist). Merge → approval; the Argo Application syncs it (selfHeal, no prune).
6. **Merge the service PR** → approval. The release pipeline builds the image, opens the dev promotion PR, auto-merges it after exact-head checks, Argo deploys the digest, smoke runs.
7. **Live acceptance:** a real order's shipment or failure produces one notice visible through the API (needs a token with `notification-reader`, held by a person: the run has no credential); the negative auth checks; the stub 503 run only after the user names the demo namespace and approves the run.

## Rollback

- Service: digest-based GitOps rollback (revert the promotion commit in box1-workloads-dev).
- Database: Flyway V1 creates new tables only; dropping the namespace's PostgreSQL loses only this service's own notices. Not done without approval.
- Consumer group: removing the service leaves group `notification` offsets; a later start resumes from them, still bounded by the floor.
- Keycloak client and DLQ topic: revert the box1-gitops PRs; Argo `keycloak` has `prune: false` and `box1-kafka` is manual, so removal on the cluster is a separate, approved step.
