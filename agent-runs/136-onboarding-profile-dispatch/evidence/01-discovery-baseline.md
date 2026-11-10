# 01 Discovery baseline (observed 2026-11-08 23:01 America/New_York = 2026-11-09T04:01Z)

Read-only: oc get (rhdh leases, configmaps, deployment, pod annotations), gh api contents of box1-gitops main, git tags of box1-templates.

## box1-templates
- main: 5663eb3 (matches the prompt's verified baseline). Line references in the prompt re-checked: PROFILES L22-25, this.vm L184, branches at L324/L328/L426/L440/L502/L522-528/L621/L652-668/L682, registerCatalog L703, index.cjs enum L8, catalog actions L27-39 - all as described.
- Newest plugin tag: onboarding-plugin-v1.2.0 -> 8537ec131d6afc49bde020f6e110aa9073bdb0ac. Plugin and script diff from that tag to main touches only scripts/test-onboarding-vm.cjs (2 lines) and scripts/validate.mjs.
- plugins/box1-onboarding/package.json 1.2.0; oci-package.json has no version field.

## Deployed plugin
box1-gitops main 4bcc9078ae6d46cd7bdae4c7cec8214221ddcb52:
```
13:      - package: oci://registry.apps.ocp.box1.org/box1-plugins/box1-onboarding-plugin@sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b!box1-scaffolder-onboarding
43:              box1.org/onboarding-plugin-digest: sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b
44:              box1.org/onboarding-plugin-revision: 8537ec131d6afc49bde020f6e110aa9073bdb0ac
```
Live rhdh/backstage-developer-hub Deployment template annotations and running Pod backstage-developer-hub-6c4c77c88d-2p24h annotations:
```
box1.org/onboarding-plugin-digest=sha256:98506a25f4adc6ef01934e77dc09510ce0d77ea0331e5fbabeb5058a0410bb8b
box1.org/onboarding-plugin-revision=8537ec131d6afc49bde020f6e110aa9073bdb0ac
```
Deployed digest = pinned digest = release of onboarding-plugin-v1.2.0 (revision 8537ec1). This is the rollback digest.

## Active onboarding runs
Leases rhdh/box1-onboard-* (name, holder, renewTime, durationSeconds):
```
box1-onboard-agentic-operations	<none>	2026-11-07T03:33:43.400000Z	1
box1-onboard-asset-service	<none>	2026-11-05T22:45:35.263000Z	1
box1-onboard-fulfillment-adapter	<none>	2026-11-05T23:43:55.219000Z	1
box1-onboard-inventory-service	<none>	2026-11-05T16:03:14.088000Z	1
box1-onboard-legacy-erp	<none>	2026-11-06T03:11:54.057000Z	1
box1-onboard-notification-service	<none>	2026-11-06T04:32:34.955000Z	1
box1-onboard-operations-console	<none>	2026-11-06T03:39:36.487000Z	1
box1-onboard-order-service	<none>	2026-11-05T07:11:37.801000Z	1
box1-onboard-scenario-controller	<none>	2026-11-06T05:45:07.965000Z	1
box1-onboard-vm-golden-check	<none>	2026-11-06T01:33:54.343000Z	1
```
Status records rhdh/box1-onboard-* (name, phase, phaseStatus, profile, updatedAt):
```
box1-onboard-agentic-operations	COMPLETE	succeeded	service	2026-11-07T03:33:43.442Z
box1-onboard-asset-service	COMPLETE	succeeded	service	2026-11-05T22:45:35.316Z
box1-onboard-fulfillment-adapter	COMPLETE	succeeded	service	2026-11-05T23:43:55.263Z
box1-onboard-inventory-service	COMPLETE	succeeded	service	2026-11-05T16:03:14.115Z
box1-onboard-legacy-erp	COMPLETE	succeeded	virtual-machine	2026-11-06T03:11:54.105Z
box1-onboard-notification-service	COMPLETE	succeeded	service	2026-11-06T04:32:35.006Z
box1-onboard-operations-console	COMPLETE	succeeded	service	2026-11-06T03:39:36.524Z
box1-onboard-order-service	COMPLETE	succeeded	service	2026-11-05T07:11:37.827Z
box1-onboard-scenario-controller	COMPLETE	succeeded	service	2026-11-06T05:45:07.998Z
box1-onboard-vm-golden-check	COMPLETE	succeeded	virtual-machine	2026-11-06T01:33:54.388Z
```
No lease is held and every record is COMPLETE: **no active onboarding** at discovery time. (Must be re-checked immediately before any Hub restart.)

## Hub action schemas
ACTION_SCHEMAS from the live Hub was **not fetched**: it requires an authenticated Hub API call, outside this run's authority. Substitute: the characterisation test loads index.cjs with Backstage stubs and records every registered action's id, description and input/output schema; that record is identical before and after the change (see 02).
