# Prepared Developer Hub inputs: `site-west` and `site-east`

**Not submitted.** Developer Hub onboarding needs approval, and every prerequisite below must be in place first. Template: `vm-instance` (`templates/vm-instance`, box1-templates#36), released in plugin 1.5.0.

## Prerequisites (none are met as of 2026-11-09)

1. Merged and released:
   - box1-gitops#132, #133 and #134;
   - box1-templates#33, #35 and #36;
   - plugin 1.5.0 pinned in `box1-gitops`, and the Hub synced.
2. `site-gateway-os` exists, was onboarded from `rhel-image-vm` with `cloudInit: true` (box1-templates#34), and has an approved, non-zero digest (#126). Its image must also provide the guest user `box1-status` (D-004).
3. The Secret `box1-ci/vm-instance-status-ssh` exists (approval item, D-004).
4. Keycloak clients `site-west` and `site-east` exist in realm `box1` (#131).
5. Capacity has been re-checked (`evidence/01-discovery.md`).

## Order

Create `site-west` first. After it is verified, create `site-east`.

## Template inputs

| Field | `site-west` | `site-east` |
| --- | --- | --- |
| Instance name | `site-west` | `site-east` |
| Source OS image repository | `site-gateway-os` | `site-gateway-os` |
| Catalog owner | `user:default/mike` | `user:default/mike` |
| Administrator SSH public key | the operator's public key | the operator's public key |
| vCPU / memory / root disk | 2 / `4Gi` / `20Gi` | 2 / `4Gi` / `20Gi` |
| Site ID | `site_ds9` | `site_spacedock` |
| Keycloak client ID | `site-west` | `site-east` |
| Keycloak token URL | `https://keycloak.apps.ocp.box1.org/auth/realms/box1/protocol/openid-connect/token` | same |
| Asset service URL | empty | empty |
| Kafka bootstrap servers | empty | empty |
| OTLP endpoint | empty | empty |

The optional endpoints are left empty because reaching them from a VM on the pod network was not verified. `box1-kafka` has Strimzi NetworkPolicies. Candidates, if #126 needs them:
- Asset service: `https://asset-service-dev.apps.ocp.box1.org`
- Kafka: `box1-kafka-kafka-bootstrap.box1-kafka.svc:9092`
- OTLP: `http://box1-collector.box1-observability.svc:4318`

Adding them later is a reviewed edit to the ConfigMap `<instance>-site`, followed by re-assembling the Secret and restarting the VM (#140 runbook).

## The single manual step (approval required)

After the task waits at `cloud_init_secret`, assemble `<instance>-dev/<instance>-cloud-init` from `<instance>-site` with box1-docs `scripts/vm-cloud-init/assemble_cloud_init_secret.py` (`runbooks/vm-cloud-init-identity.md`, box1-docs#147). Then resubmit the same parameters.

Equivalent scaffolder API request (POST `/api/scaffolder/v2/tasks`):

```json
{"templateRef":"template:default/vm-instance","values":{"name":"site-west","source":"site-gateway-os","owner":"user:default/mike","adminSshPublicKey":"<public key>","cpuCores":2,"memory":"4Gi","rootDiskSize":"20Gi","siteId":"site_ds9","keycloakClientId":"site-west","keycloakTokenUrl":"https://keycloak.apps.ocp.box1.org/auth/realms/box1/protocol/openid-connect/token","assetServiceUrl":"","kafkaBootstrapServers":"","otlpEndpoint":""}}
```
