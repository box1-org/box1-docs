# Discovery (read-only), 2026-11-09 00:00–00:30 EST

At about 00:29 EST the cluster API rejected the session (`the server has asked for the client to provide credentials`). Every cluster observation below was made before that. Nothing was changed on the cluster.

## Dependencies

All are unmerged PR stacks. None is delivered to `main`.

| Issue | PRs | State |
| --- | --- | --- |
| #136 | box1-templates#33 | open; plugin 1.3.0 not released |
| #137 | box1-templates#35 (head `6d4eef4`), box1-gitops#133 (head `59e1ef0`) | open |
| #139 | box1-gitops#132 | open |
| #140 | box1-templates#34 (`cloudInit` parameter), box1-docs#147 (runbook and script) | open; no image with cloud-init has been built |
| `site-gateway-os` (#126) | — | **does not exist.** `gh repo view box1-org/site-gateway-os` reports "Could not resolve". `box1-workloads-dev` has no `workloads/site-gateway-os`, and there is no image stream |

Per the prompt's stop conditions, live acceptance is blocked: a dependency is not delivered, and there is no approved source digest.

## Cluster

- OpenShift `5.0.0-rc.7`, one node (`quark.host.box1.org`).
- `kubevirt-hyperconverged-operator.v5.0.0`.
- `rhdh-operator.v1.9.7`.
- `openshift-pipelines-operator-rh.v1.24.3`.

## Capacity (node `quark.host.box1.org`)

| Resource | Observed | Two instances (2 vCPU, 4Gi, 20Gi each) |
| --- | --- | --- |
| CPU requests | 28562m of 31500m allocatable (90%); about 2.9 cores free | about 400m more (each 2-vCPU VM's virt-launcher requests 200m, as observed on `legacy-erp` and `vm-golden-check`). Fits; CPU limits are already 348% overcommitted |
| Memory requests | 101.9 GB of 133.8 GB allocatable (76%); about 31.9 GB free | about 8.5 GiB more (4372Mi per 4Gi VM, observed) → about 83% |
| Memory in use (`oc adm top node`) | about 92.3 GiB (72%) | estimate about 80% if each guest uses its full 4Gi |
| LVMS `vg1` free (`capacity.topolvm.io/vg1`) | 844044959744 bytes, about 786 GiB; 45 `lvms-vg1` PVs total 924Gi | 40Gi |

**Conclusion:** two instances fit by requests. Memory is the tightest resource. A third throwaway instance for the decommission test, plus a `rhel-image-vm` regression VM, would bring requests to about 90% memory. Run those one at a time and remove each before the next. These are estimates; no instance has been measured.

## Other observations

- **Active onboardings:** none. All 10 `rhdh/box1-onboard-*` records are `COMPLETE`.
- **Hub ServiceAccount:** `rhdh/developer-hub-onboarding`. `ci-vm-deploy` exists in `box1-ci`.
- **Fixture site IDs:** `site_ds9` ("Deep Space Nine, Promenade outlet") and `site_spacedock` ("Earth Spacedock") are defined in `box1-org/scenario-controller` `src/main/java/org/box1/scenario/fixtures/Fixtures.java` (commit `92d66b9`). They are **not** in `box1-org/box1-ops-contracts` (`main` `7b7fbac`, all branches searched), whose fixtures use `site_nyc` and `site_bos`. Both IDs match the #140 pattern `^[a-z][a-z0-9_]{1,62}$` and the ops-contracts `SiteId` pattern `^site_[A-Za-z0-9_-]{1,64}$`.
- **Keycloak:** the `box1` realm issuer is `https://keycloak.apps.ocp.box1.org/auth/realms/box1`, and the token endpoint is `…/protocol/openid-connect/token` (from `.well-known`). No `site-west` or `site-east` clients were checked or created (#131).
- **Disk pairing** (see D-002): `vm-golden-check`'s DataVolume pins the `c8abaae` disk `f45a99…`, while its approved revision `21a898e` has disk `6fa3fe…`. The `box1-bootc-disk` Task labels disks with `box1.org/bootc-image`.
- **Guest access:** `legacy-erp` uses `deploy-access.yaml` (ci-vm-deploy, portforward) and `box1-deploy` via a second `accessCredentials` entry. The #140 rule forbids that entry for instances; see D-004.
- **`Prune=false,Delete=false` PVCs:** `legacy-erp-data`, `asset-service-postgres`, `notification-service-postgres`.
