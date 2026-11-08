# Hawtio Online: GitOps-managed console showing the fulfillment-adapter Camel routes

**Date:** 2026-11-08 (America/New_York), merges 12:35–13:56 EST, final check 16:57 EST. Cluster timestamps below are UTC (EST + 5 h).

**Status:** Delivered and live.
- The Hawtio work item and its acceptance criterion in [box1-docs#114](https://github.com/box1-org/box1-docs/issues/114) are ticked. #114 itself stays open for its other Dev Spaces items.
- One security problem is still open: [box1-docs#117](https://github.com/box1-org/box1-docs/issues/117). The Hawtio gateway logs users' bearer tokens.

Background: the Dev Spaces decisions that led to this work are in [#114](https://github.com/box1-org/box1-docs/issues/114). The fulfillment adapter itself is described in [2026-11-05-fulfillment-adapter-delivery.md](2026-11-05-fulfillment-adapter-delivery.md).

## Outcome

Hawtio Online now runs on the cluster as an OpenShift console app. It shows the live Camel routes and JVM management data of `fulfillment-adapter` in `fulfillment-adapter-dev`. The user confirmed in the browser that **Connect** opens the pod and shows its routes.

Hawtio gives developers a view into the running integration (route state, exchanges, JVM data) without `oc exec` or port-forwards. It is the Hawtio piece of the Dev Spaces developer environment (#114).

| Item | Value |
|---|---|
| Operator (OLM, manual InstallPlan, GitOps-managed) | Red Hat build of HawtIO `red-hat-hawtio-operator.v2.0.0-0.1785112309.p`, channel `v2`, catalog `redhat-operators-v422`, namespace `hawtio`, AllNamespaces OperatorGroup |
| Console | `Hawtio/hawtio-online` (`hawt.io/v2`), `type: Cluster`, 1 replica. Images `hawtio-rhel9:2.4.0` and `hawtio-gateway-rhel9:2.4.0` |
| URL | `https://hawtio-online-hawtio.apps.ocp.box1.org` (reencrypt Route). The operator also adds a ConsoleLink in the OpenShift console |
| Login | OpenShift OAuth. The operator creates the OAuthClient. Users see only pods in namespaces they can access |
| Hawtio → pod trust | Client certificate `CN=hawtio-online.hawtio.svc`, signed by the cluster service CA (`service-serving-signer`), Secret `hawtio-online-tls-proxying`, renewed every 24 h |
| Agent | `camel-quarkus-jolokia` 3.40.0 (Jolokia 2.6.2) in `fulfillment-adapter`, HTTPS with client-certificate authentication on container port `jolokia` (8778) |
| GitOps | `box1-gitops` Applications `hawtio-operator` (`platform/hawtio/operator`) and `hawtio` (`platform/hawtio/instance`), both manual sync, following the Dev Spaces pattern |

## Starting baseline

These are read-only observations from 2026-11-08, before any change:

- No Hawtio, Jolokia or JMX-over-HTTP configuration existed anywhere in box1-org (recorded in #114's baseline).
- `fulfillment-adapter` was a Quarkus 3.40 / Camel Quarkus service with no management dependencies. Its Deployment sets `automountServiceAccountToken: false`, so the pod had no copy of the service CA.
- The catalog `redhat-operators-v422` offered package `red-hat-hawtio-operator`, channel `v2`, with AllNamespaces install supported.

## What changed

| PR | Merge | Change |
|---|---|---|
| [box1-workloads-dev#178](https://github.com/box1-org/box1-workloads-dev/pull/178) | `2e69cbc` | `fulfillment-adapter` Deployment: container port `jolokia` 8778. The `openshift-service-ca.crt` ConfigMap is mounted read-only at `/var/run/secrets/box1/service-ca`, and `QUARKUS_CAMEL_JOLOKIA_KUBERNETES_SERVICE_CA_CERT` points at it. The token stays unmounted; PSA `restricted` and the read-only root filesystem are unchanged |
| [box1-gitops#117](https://github.com/box1-org/box1-gitops/pull/117) | `6e33ac0` | `platform/hawtio/operator` (Namespace, OperatorGroup, Subscription with `installPlanApproval: Manual`). `platform/hawtio/instance` (Hawtio CR, and a Role that lets Argo CD manage `hawtios`). Two manual-sync Applications. README covering what a service needs to appear in Hawtio |
| [fulfillment-adapter#8](https://github.com/box1-org/fulfillment-adapter/pull/8) | `39a898e` | Adds `camel-quarkus-management` (Camel MBeans) and `camel-quarkus-jolokia`. Port 8778, and in prod the client principal `cn=hawtio-online.hawtio.svc` (overridable through `JOLOKIA_CLIENT_PRINCIPAL`). All 103 tests pass |
| [box1-workloads-dev#180](https://github.com/box1-org/box1-workloads-dev/pull/180) | `b240888` | Promotion by the release pipeline (`fulfillment-adapter-release-2kwfp`): image `sha256:c0e3feb8…` built from `39a898e`. The build, security scan, smoke, fulfillment API smoke and promote tasks all succeeded. The scan reported 0 critical vulnerabilities |
| [box1-gitops#119](https://github.com/box1-org/box1-gitops/pull/119) | `369559e` | Raises the console's memory limit from 200Mi to 512Mi (request 128Mi) after the gateway was OOM-killed (see below) |

The workload change (#178) was merged before the app change (#8). This way the image that requires the service CA could not roll out before the CA was mounted.

**Design decisions:**

- **Cluster mode, not namespace mode.** One console discovers Jolokia pods in every namespace the logged-in user can see. A project selector was not set.
- **Only Hawtio can call the agent.** On Kubernetes, Jolokia accepts only HTTPS clients whose certificate is signed by the service CA. The client principal additionally limits access to Hawtio's certificate. Without that setting the agent has no allowed principal, and every call is rejected. Off-cluster (local dev, tests) the agent binds to loopback only.
- **Discovery by port name.** Hawtio finds pods by a container port named `jolokia`. No labels or annotations are needed.
- **The same resource limits for both containers.** `spec.resources` on the Hawtio CR applies to both the nginx and gateway containers.

**Made outside Git, with the user's approval in chat:**
- Merges of all four PRs except #180, which the pipeline auto-merged.
- Argo syncs of `hawtio-operator` and `hawtio`, then a second `hawtio` sync after #119. Each was triggered by setting the Application `operation`.
- InstallPlan `install-mzl5r` approved after checking that its CSV was `red-hat-hawtio-operator.v2.0.0-0.1785112309.p`.

## Incident during rollout: Connect failed (gateway OOM kill)

**Symptom:** the user could see the Hawtio discover page listing the adapter pod, but **Connect** did nothing.

**Cause:**
- The first CR used the operator's example limit of 200Mi, which `spec.resources` applies to the gateway container as well as nginx.
- The gateway was killed by a memory-cgroup OOM: exit code 137 at 18:49:10 UTC, from the node journal. It restarted 3 times.
- While it was down, nginx returned `502` with `no live upstreams` for the proxy calls that Connect makes.

**Fix:** box1-gitops#119 set requests to 200m / 128Mi and limits to 1 CPU / 512Mi, and `hawtio` was resynced. The new pod `hawtio-online-7d9fc86cb-tv6n7` has had 0 restarts since. The user then confirmed that Connect works.

**Found while diagnosing it:** at the default `info` level, the gateway logs full request headers, including each user's OAuth bearer token. The operator offers only `info` and `debug` log levels, so this can't be turned off from the CR. These lines are not forwarded to Loki, because the `hawtio` namespace is not collected (see [2026-11-06-loki-centralized-logging.md](2026-11-06-loki-centralized-logging.md)). The tokens are still readable by anyone who can read pod logs in `hawtio`. Filed as [box1-docs#117](https://github.com/box1-org/box1-docs/issues/117).

## Validation and evidence

All checks ran against the live cluster. Requests went through the Hawtio Route's proxy path `/management/namespaces/fulfillment-adapter-dev/pods/https:<pod>:8778/jolokia/`.

| Check | Result |
|---|---|
| Operator | InstallPlan `install-mzl5r` approved; CSV `Succeeded` |
| Console | `Hawtio/hawtio-online` phase `Deployed`. Both Applications `Synced` / `Healthy` |
| Client certificate | Subject `CN=hawtio-online.hawtio.svc`, issuer `service-serving-signer` |
| Authenticated read via Hawtio | Jolokia `search` for `org.apache.camel:type=routes,*` with a cluster-admin token: `status 200`, **10 routes**. First verified on image `c0e3feb8…`; re-run at 21:57 UTC on the current pod (see below) with the same result |
| Anonymous read via Hawtio | The same request without a token returned **403**, both times |
| Direct call to the pod without a client certificate | `https://<pod>:8778/jolokia/` returned **403** |
| Browser | The user logged in through OpenShift OAuth and Connect showed the adapter's routes (after #119) |
| Resource use at 21:57 UTC | Gateway 316Mi of its 512Mi limit, nginx 119Mi, operator 55Mi. CPU under 0.03 core |

**Not tested or not established:**

- **Access by a non-admin user:** that a user without access to `fulfillment-adapter-dev` cannot connect to the pod was not tested. All checks used a cluster-admin token.
- **Rotation:** the 24 h client-certificate rotation has not happened yet, so it was not observed.
- **Operating routes:** route stop/start and other write operations through Hawtio were not exercised.
- **Gateway memory over time:** the gateway reached about 60% of its new limit with one connected pod after about 3 hours. Its behavior with more Jolokia pods or a longer uptime is unknown.
- **Vendor support:** whether Red Hat supports HawtIO operator 2.0.0 on OpenShift 5.0.0-rc.7 is not established.

## Final operational state

- **Management:**
  - Argo CD runs `hawtio-operator` and `hawtio` from `box1-gitops` `main`, with manual sync. Both are `Synced` / `Healthy`; the last change to `platform/hawtio` is `369559e`. There is no manual override.
  - The fulfillment adapter's Argo CD app `fulfillment-adapter` is `Synced` / `Healthy`.
- **Adapter image:** the adapter has since moved on to later releases from other work: [fulfillment-adapter#10](https://github.com/box1-org/fulfillment-adapter/pull/10) (Camel routes converted to YAML DSL) and [fulfillment-adapter#9](https://github.com/box1-org/fulfillment-adapter/pull/9) (Dev Spaces devfile). The running image is `sha256:ee64b444…`. It still includes Jolokia and the `jolokia` port, and the 21:57 UTC check above ran against it.
- **Other services:** only `fulfillment-adapter` is visible in Hawtio. The other six Box1 services don't use Camel. For them, Hawtio would show only JVM data, which mostly overlaps the existing metrics. Adding them needs an agent in each app (not `camel-quarkus-jolokia`) and the same Deployment changes as #178. A shared kustomize component would be the natural way to do that. Nothing has been decided.
- **Upgrade caveat:** the Subscription is set to manual approval, so operator upgrades wait for a reviewed InstallPlan.

## Recovery and follow-ups

- **Stop exposing the adapter:**
  - Revert box1-workloads-dev#178's port; Hawtio discovers pods by that port name.
  - Or remove `camel-quarkus-jolokia` from the app.
  - The agent needs the service CA mount to start, so that mount must stay as long as the dependency does.
- **Remove the console:** delete the `hawtio` Application with cascade, then `hawtio-operator`. Then delete the CSV, and the CRD if it is no longer needed.
- **Roll back the memory change:** revert box1-gitops#119 and sync `hawtio`. Not recommended: the 200Mi limit caused the OOM kills.
- None of these paths was exercised. The install and agent requirements are in [`platform/hawtio/README.md`](https://github.com/box1-org/box1-gitops/blob/main/platform/hawtio/README.md).
- **Follow-up:** stop the gateway logging bearer tokens ([box1-docs#117](https://github.com/box1-org/box1-docs/issues/117)).
- **Follow-up:** the remaining Dev Spaces items, including the devfile's "open Hawtio" command and the runbook ([box1-docs#114](https://github.com/box1-org/box1-docs/issues/114)).
- **Not filed:** extending Hawtio to the non-Camel services. This waits on the user's decision.
