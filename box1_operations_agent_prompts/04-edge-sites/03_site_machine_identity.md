# Edge sites 03 — Per-site machine identity (Keycloak clients and KafkaUsers)

> **Identity work in `box1-gitops`, asset-service and the site image.** Each site gets its own machine identity for HTTPS and, once Kafka authentication exists, for Kafka. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Creating a Keycloak client, copying its secret, or creating any Secret needs approval. Record how it is provisioned, never its value.
- No credential goes in Git, the OS image, VM manifests, logs, evidence or handoffs.
- GitOps changes go through PRs that state what merging deploys. The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not use Chrome.

**Issue:** [box1-docs#131](https://github.com/box1-org/box1-docs/issues/131), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- [#140](https://github.com/box1-org/box1-docs/issues/140) (`../03-golden-path/03_vm_cloud_init_nocloud.md`): the cloud-init credential delivery and its assembly script. #126's golden-path comment notes that this issue's credential delivery must be aligned with #140; this prompt does that.
- [#138](https://github.com/box1-org/box1-docs/issues/138): the site instances, for live checks.
- `04_site_status_sites_map.md` uses the asset-service claim check. Implement the check here or there, but in one place; record which.
- **The Kafka half is blocked on [#71](https://github.com/box1-org/box1-docs/issues/71)** (listener authentication and ACLs). Do the Keycloak half first.

## Mission

Give `site-west` (`site_ds9`) and `site-east` (`site_spacedock`) each a confidential client-credentials client in the `box1` realm, with a token claim that binds it to its `siteId`, delivered to the VM without baking it into the image. After #71, give each site a KafkaUser whose ACLs limit what it may produce and read.

## Verified baseline (observed 2026-11-09; verify before relying)

**Keycloak** (`box1-gitops` main `4bcc907`, `platform/identity/keycloak/`)
- RH-SSO 7.6 through `rhsso-operator`, API `keycloak.org/v1alpha1`. Argo Application `keycloak` (selfHeal on, `prune: false`).
- `realm/realm.yaml` L1–25 defines the `KeycloakRealm`. Each client is one `KeycloakClient` file listed in `realm/kustomization.yaml` L1–17.
- Issuer: `https://keycloak.apps.ocp.box1.org/auth/realms/box1`.
- README L55–58: realm roles also had to be added through the Admin API because the operator did not apply them on realm update.
- **Client-credentials precedent:** `scenario-controller-client.yaml` L1–64: confidential, `serviceAccountsEnabled: true`, `fullScopeAllowed: false`, pinned `client.id` UUID, `defaultClientScopes: [roles]` (L33–36), an audience mapper (L38–46), and `scopeMappings` plus `serviceAccountClientRoles` (L47–57).
- The operator generates `keycloak-client-secret-<client>` in namespace `keycloak`. Copying it to a consumer is a manual, approved step (L4–6). There is no secret manager.
- Only `oidc-audience-mapper` is in use. **No custom-claim mapper exists yet.**

**asset-service** (main `95bf5c8`)
- `application.properties` L40–66: `quarkus.oidc.application-type=service`, `token.audience=asset-service`, roles from `resource_access/asset-service/roles`. **Paths not listed in a permission set are denied** (L49–50).
- `ClientAccess.java` L19–50 checks `azp`.
- [#62](https://github.com/box1-org/box1-docs/issues/62) is open: no machine identity can hold `telemetry-writer` today. The sites send readings through Kafka, not the HTTP ingestion API, so #62 is related but not required here.

**Credential delivery** (#140, owner decision 2026-11-08): Git holds a non-secret `<instance>-site` ConfigMap; a script in `box1-docs` assembles the `<instance>-cloud-init` Secret outside Git, writing the client secret to a file readable only by the site service user (proposed `/etc/box1/credentials/keycloak-client-secret`, mode 0400). The VM stays Halted until the Secret exists. See [PR #147](https://github.com/box1-org/box1-docs/pull/147) for its current state.

**Kafka**: one `plain` listener, no authentication or authorization; the User Operator is enabled but there are no KafkaUsers, and Argo's RBAC does not cover KafkaUsers (`platform/kafka/rbac.yaml` L9–11).

## Decided design

From the issue, #126's decisions and #140's decision.

**Keycloak (Keycloak half)**
- Clients `site-west` and `site-east`, one `KeycloakClient` file each, following the `scenario-controller` precedent: confidential, service accounts on, `fullScopeAllowed: false`, `defaultClientScopes: [roles]`, an audience mapper for `asset-service`, and only the client role the status write needs (proposed `site-reporter` on `asset-service`).
- A hardcoded-claim protocol mapper adds `siteId` (`site_ds9`, `site_spacedock`) to the access token. Confirm RH-SSO 7.6's operator applies it; if not, record the fallback (for example mapping `azp` to `siteId` in asset-service configuration) as a decision.
- asset-service accepts a status write only when the token's `siteId` claim equals the path `siteId` and the role is present. Anonymous writes and mismatches are rejected.

**Credential delivery**
- Use #140's flow: the operator-generated secret is the source; the #140 assembly script writes it into the cloud-init Secret. The credential is never in the image.
- Rotation: regenerate the client secret, re-run the assembly script, restart or re-create the VM. Document it in the #140 runbook or a linked section.

**Kafka half (after #71)**
- A `KafkaUser` per site with ACLs: write to `box1.telemetry.events.v1` and the site topic; read the pick-list source with a site-specific consumer group.
- **ACLs cannot filter by message content.** The pick-list source (`box1.inventory.events.v1`, keyed by `orderId`) carries every site's reservations, so a site can read others' reservations unless a per-site topic or a filtering service is added. Record what is accepted.
- "A site may write only its own `siteId`": the producer identity is the KafkaUser; consumers (`05`, `06`) reject or dead-letter an event whose `siteId` does not match the producing principal. That needs the principal to reach the consumer (for example a header set by the gateway and checked against the ACL'd topic, or per-site topics). Decide and record.
- Kafka credentials reach the VM by the same out-of-Git flow.

## Scope and guardrails

**In scope**
- `box1-gitops` `platform/identity/keycloak/realm/`: two client files and the kustomization entry.
- asset-service: the claim check on status writes (or hand it to `04`).
- The credential section of the #140 runbook.
- After #71: KafkaUsers, ACLs, the Argo RBAC change for KafkaUsers, and the consumer-side `siteId` check in `05` and `06`.

**Out of scope**
- Kafka listener authentication itself (#71).
- #62's telemetry-writer identity.
- Building the image or creating instances.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #131 only with the evidence named.

- [ ] Each site authenticates to asset-service with its own client, and a token for site-west is rejected when writing site-east's status.
  - Evidence: from each guest, a token request (redacted, showing only decoded `azp`, `siteId` and roles), a successful own-status write, and a `403` for the other site's path; an anonymous request returning `401`.
- [ ] The OS image digest contains no site credentials; rotating a site's credential needs no image rebuild.
  - Evidence: a search of the image filesystem (`podman run … find`/`grep`) for the secret's file path and for client-secret patterns; a rotation run (approval) showing the same booted digest before and after and a successful write with the new credential.
- [ ] (After #71) Each site connects to Kafka as its own KafkaUser, and a write outside its ACL is rejected.
  - Evidence: KafkaUser status, producer logs, and an authorization failure for a disallowed topic.
- [ ] (After #71) An event claiming the other site's `siteId` is rejected or dead-lettered by consumers.
  - Evidence: a crafted event from site-west claiming `site_spacedock`, and the consumer's rejection or DLQ record.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/131-site-identity/`.

**Discovery must cover**
- The RH-SSO operator's support for hardcoded-claim mappers on `KeycloakClient`.
- #140's delivered script, Secret format and credential path; #71's state.
- asset-service's permission sets and `ClientAccess`.
- How the site agent will request tokens (endpoint reachability from the guest: Route or internal Service).

**Design decisions to record**
- Client role name and claim name.
- Where the claim check lives (`03` or `04`).
- Token endpoint the guest uses and its TLS trust (the service CA disk or public CA).
- Kafka ACL scope, the pick-list exposure accepted, and the consumer-side check (after #71).

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 3 Implementation | Negative tests for anonymous, wrong-site and missing-role writes |
| 5 Review | Security pass confirms no credential in Git, image, logs or evidence |
| 6 Delivery | Clients reconciled by Argo; secrets delivered through the #140 flow |
| 7 Live acceptance | The first two criteria; the Kafka criteria marked `blocked` on #71 if it is still open |

**Verification scenarios**
- Expired token; wrong audience; token from a non-site client; secret rotated while the site runs; cloud-init Secret missing.

**Stop conditions**
- Creating the clients or copying secrets is not approved.
- The operator cannot express the claim and no fallback is accepted.
- #140's delivery is not merged.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the client files, claim and role names, the rotation procedure, the negative-test evidence, the Kafka half's status against #71, and rollback (revert the client PR; the operator-generated secrets then need manual removal, which needs approval).

Tick the completed items on #131.
