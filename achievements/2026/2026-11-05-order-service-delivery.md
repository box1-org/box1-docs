# Order service: first service delivered through the enforced security gate

**Date:** 2026-11-05 (America/New_York)
**Status:** Delivered and live. Acceptance is partial, see below. Tracked in [box1-docs#11](https://github.com/box1-org/box1-docs/issues/11), closed on the owner's instruction, with follow-ups #40 to #44. This was the first pilot of the `frontier` execution profile. The run state, decisions, evidence and pilot log are in [`agent-runs/11-order-service/`](../../agent-runs/11-order-service/), merged in [#48](https://github.com/box1-org/box1-docs/pull/48).

## Outcome

`order-service`, Box1's first domain service, runs in `order-service-dev`. It was delivered through Tekton and Argo CD with the ACS and TPA security gate set to `gate`. It is also the first Box1 release whose image was rejected or accepted by policy before promotion.

| Item | Value |
|---|---|
| Release | `order-service-release-6skld` |
| Source | `box1-org/order-service` `8fda087` |
| Image | `image-registry.openshift-image-registry.svc:5000/box1-ci/order-service@sha256:c90bae8aeb73537dda149be3713744c579fb06d6837e1e21d8d50c3a5ef605c8` |
| GitOps | `box1-workloads-dev` `359c711` ([#59](https://github.com/box1-org/box1-workloads-dev/pull/59)), Argo `order-service` Synced/Healthy |
| SBOM | TPA `urn:uuid:01a1adcc-10b3-730e-9e2d-dcb4b29435d2` |
| Route | `https://order-service-dev.apps.ocp.box1.org` |

**The service:** Quarkus 3.40 on Java 21, PostgreSQL, and a transactional outbox publishing to AMQ Streams.

- An idempotent create API with RFC 9457 Problem errors.
- An immutable order timeline.
- Lifecycle consumers for inventory and shipment events, with a dead-letter topic.
- JSON logs carrying order, trace and correlation IDs, plus business metrics.

Along the way, the work restored TPA storage, gave ACS access to the internal registry, fixed `roxctl` trust in the gate, and refreshed the template's base image. Every Golden Path service uses those paths.

## Starting baseline

- `order-service` was a template scaffold running greeting endpoints at the issue's start, and no order domain existed. The `orders-service` example named in the prompt no longer existed anywhere, so its guard requirement was superseded.
- Releases ran with `security-gates: disabled`. `SECURITY-GATES.md` listed registry integration and exact-digest reports as unverified.
- **TPA could not store anything.** NooBaa's only backing store had been `Rejected` since 2026-11-01. Its agent pod was evicted on low ephemeral storage and never recreated, while NooBaa still reported `Ready`.
- **ACS could not scan internal images:** `no matching image registries found`.
- `scanner-v4-matcher` had restarted 665 times in about 4.5 days.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Contracts | [box1-ops-contracts#3](https://github.com/box1-org/box1-ops-contracts/pull/3) | `0b25a9f` | Complete v1 Order OpenAPI, events and fixtures |
| Contracts | [box1-ops-contracts#4](https://github.com/box1-org/box1-ops-contracts/pull/4) | `bea6c7b` | Timeline `sequence` is global, by owner decision |
| Platform | [box1-gitops#52](https://github.com/box1-org/box1-gitops/pull/52) | `6e0fc26` | `box1.order.dlq.v1` dead-letter topic |
| Runtime | [box1-workloads-dev#50](https://github.com/box1-org/box1-workloads-dev/pull/50) | `01051d5` | Kafka and database settings, scoped PostgreSQL NetworkPolicy, resources |
| Service | [order-service#1](https://github.com/box1-org/order-service/pull/1) | `749ef13` | Order domain, outbox, lifecycle consumers, tests, runbook |
| Gate | [order-service#2](https://github.com/box1-org/order-service/pull/2) | `e183578` | Release runs `security-gates: gate` |
| ACS | [box1-gitops#53](https://github.com/box1-org/box1-gitops/pull/53) | `6626781` | Pull-only `acs-registry-reader` identity in `box1-ci` |
| Image | [order-service#3](https://github.com/box1-org/order-service/pull/3) | `a749ef8` | Current base image digest, Guava override for CVE-2026-102554 |
| Gate | [box1-gitops#54](https://github.com/box1-org/box1-gitops/pull/54) | `36e305d` | `roxctl` trusts Central's CA, prints its errors, separates scan failure from rejection |
| ACS | [box1-gitops#55](https://github.com/box1-org/box1-gitops/pull/55) | `37f429a` | Matcher requests 1 CPU and 3 GiB, limits 2 CPU and 6 GiB |
| Template | [box1-templates#23](https://github.com/box1-org/box1-templates/pull/23), [#24](https://github.com/box1-org/box1-templates/pull/24), [#25](https://github.com/box1-org/box1-templates/pull/25) | `45099ac`, `cfa83ce`, `591feda` | Onboarding accepts the scoped NetworkPolicy, runtime baseline from #50, current base image |
| Service | [order-service#4](https://github.com/box1-org/order-service/pull/4) | `0920f9a` | Served OpenAPI matches the contract, relative `Location`, `order-api-smoke`, runbook rollback advice |

**Made outside Git, with approval:**

- **Deleted the evicted NooBaa agent pod** `noobaa-default-backing-store-noobaa-pod-3aa907b4`. The operator recreated it on the same 50 GiB PVC, and the store returned to `Ready`/`OPTIMAL` within about 46 seconds.
- **Created the ACS image integration** for `image-registry.openshift-image-registry.svc:5000` in Central, done by the owner, with **TLS verification off** (#44).
- **Granted the owner's Keycloak user `Admin`** through the `acs-oidc-config` declarative provider. The owner applied it, and it is not in Git.

**Decisions with consequences:**

- **Relative `Location` instead of trusting forwarded headers.** The contract allows `uri-reference`, and trusting `X-Forwarded-*` would let callers influence the value.
- **The order smoke writes nothing.** A write on every release would accumulate in immutable history, so **a broken create path would still pass smoke.**
- **API authentication was deferred** (#40). Order data is readable on the LAN.
- **The database credential stays inline.** Vault is planned (#41). The specifics are withheld because this repository is public.
- **The gate fails on fixable Important or Critical CVEs.** This is RHACS's `Fixable Severity at least Important` policy. Unfixed Important CVEs pass, so expect the gate to start failing when Red Hat publishes fixes for packages in the base image.

## Validation and evidence

Details are in [`evidence/09-release.txt`](../../agent-runs/11-order-service/evidence/09-release.txt) and [`review-findings/release.md`](../../agent-runs/11-order-service/review-findings/release.md).

| Test | Expected | Observed |
|---|---|---|
| Local suite with containers | Pass | 64 unit and 8 integration tests, Checkstyle and SpotBugs clean, on each merged change |
| Final release `6skld` | All stages pass | Build, `gate` (scan exit 0, check exit 0, SBOM accepted), promote, smoke, `order-api-smoke`: all Succeeded |
| Running image | Promoted digest | Pod imageID `sha256:c90bae8a…`, `/api/info` `gitRef` `8fda087` |
| Idempotent create through the Route | One order per key | First order: 201, then 200 ×9, changed body 409. Re-run on `513c366d`: 201, 200, 200, 409. Replay on the final image: 200 with `Location: /api/v1/orders/…` |
| Served OpenAPI | Contract response codes | POST 200, 201, 400, 409. GET by id 200, 404. Request and 201 examples present |
| Event publication | Published once | First order's `order.placed.v1` read from `box1.order.events.v1`. Outbox metrics showed published 1, pending 0 for the second order |
| Gate rejects a bad image | Rejection, no promotion | TaskRun `order-service-gate-negative-test` on `fb669bff…` (14 `FAIL_BUILD` violations): `check exit=1`, deployed digest unchanged |
| TPA write | Accepted | SBOM uploads 201 on every release after the backing store recovered |
| Independent Release review | — | Conditional verdict, 9 findings. The served OpenAPI, smoke and `Location` findings were fixed and verified live |

**Ledger:** 11 `live_verified`, 22 `deployed`, 1 `blocked`, 1 `superseded`. Some entries' limitation notes describe intermediate states. The deployment references and this log describe the final state.

**Not verified:**

- **`ORD-LIVE-LIFECYCLE`:** one order followed past `SUBMITTED`. Blocked because the inventory and shipment services do not exist.
- **Consumer, broker outage, restart and dead-letter behavior** on the cluster. These are proven locally only.
- **Rollback.** The runbook says to roll forward.
- **A full PipelineRun stopping after a policy rejection.** The negative test ran the Task alone.
- **`observe` mode.**
- **Trace export.** It is off, and correlation is proven through IDs only.

## Final operational state

- **`order-service`:** Argo `order-service` at `359c711`, Synced/Healthy, one pod on the digest above. PostgreSQL is in the same namespace on a 5 GiB volume. Topics `box1.order.events.v1` and `box1.order.dlq.v1` are Ready under the `box1-kafka` Application.
- **Release pipeline:** defined in `order-service/.tekton/release.yaml` on `main`, with `security-gates: gate`, read from the default branch.
- **Gate task:** `box1-security-gates` is managed by `pipelines-ci`, which has no automated sync.
- **ACS:** RHACS 4.11.6, with the matcher on the new resources. It restarted twice after the change, cause not established (#43). The registry integration and the OIDC role mapping are managed in Central and the Secret, outside Git.
- **TPA:** writes work. **The NooBaa recovery was a manual pod deletion, and the next eviction can repeat the outage** (#43).
- **Test data left live:** orders `ord_24a3627c742847c4ad6ef3670e21ea5a` and `ord_105f4cdf614f47208b6a3a14863855c4`, which hold `box1_orders_stuck` at 2. There are also several availability-probe and negative-test SBOMs in TPA, and the negative-test TaskRun in `box1-ci`.

## Recovery and follow-ups

**Recovery:**

- **Roll forward** with a new release.
- **Reverting** the promotion commit in `box1-workloads-dev` restores `sha256:513c366d…`, which passed the gate. It skips the gate, and it is untested.
- **Migration `V1`** is forward-only.

**Lessons, from the [pilot log](../../agent-runs/11-order-service/pilot-log.md):**

- **Healthy pods were not working services.** "ACS pods running, TPA HTTP 200" hid a dead backing store and a missing registry integration.
- **The client matters.** An API test scan missed `roxctl`'s CA failure.
- **GitHub returned 404 and 500** to Pipelines as Code check-run calls for over an hour. Runs were orphaned, promote failed two releases that had passed the gate, and `/retest` did not recover a push. A new commit after recovery did.

**Follow-ups:**

- [#40](https://github.com/box1-org/box1-docs/issues/40): API authentication.
- [#41](https://github.com/box1-org/box1-docs/issues/41): Vault and the database credential.
- [#42](https://github.com/box1-org/box1-docs/issues/42): the release flow.
  - Security mode default.
  - Argo `OutOfSync` on orphaned ConfigMaps.
  - Gate results kept per run and policy in Git.
  - Bypass routes.
  - Pipelines as Code start failures.
- [#43](https://github.com/box1-org/box1-docs/issues/43): matcher memory and restarts, node ephemeral storage, NooBaa eviction recovery and alerting.
- [#44](https://github.com/box1-org/box1-docs/issues/44): Central trust for the service CA, to turn registry TLS verification back on.
- **Cleanup, untracked:**
  - The `stackrox/roxctl-token` pod. Check its logs for a token, and rotate if one is there.
  - Merged `box1-gitops` branches.
  - The test orders and probe SBOMs above.
