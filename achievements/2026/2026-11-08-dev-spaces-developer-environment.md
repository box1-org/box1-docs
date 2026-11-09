# Dev Spaces developer environment: Box1 UDI, devfiles, remote dev, JVM debug and nested containers

**Date:** 2026-11-08 (America/New_York), first merge 12:59 EST, #114 closed 21:05 EST. Cluster timestamps quoted from the issue are UTC (EST + 5 h).

**Status:** Delivered.
- Tracking issue [box1-docs#114](https://github.com/box1-org/box1-docs/issues/114) is closed with every work item and acceptance criterion checked.
- Two known problems are split out and open: [#120](https://github.com/box1-org/box1-docs/issues/120) (workspace cleanup jobs rejected when other workspaces exist) and [#121](https://github.com/box1-org/box1-docs/issues/121) (Testcontainers not run in CI).
- Hawtio Online, also part of #114, has its own log: [2026-11-08-hawtio-online.md](2026-11-08-hawtio-online.md). The demo-day retirement that closed the service rollout is in [2026-11-08-demo-day-decommission.md](2026-11-08-demo-day-decommission.md).

## Outcome

"Open in Dev Spaces" on a Box1 service now gives a workspace built for Box1 work instead of the operator defaults. From the workspace a developer can:

- **Run Tekton pipelines** for the pushed HEAD (`box1-pipeline validate|logs|list`) and follow their logs.
- **Run uncommitted code on the cluster** with Quarkus remote dev in a per-user sandbox namespace (`box1-remote-dev deploy|sync|delete`), without touching `<service>-dev`.
- **Debug JVMs** from VS Code: always in the sandbox, and in `<service>-dev` for services that opt in to the `jvm-debug` kustomize component (inventory-service and order-service today).
- **Run containers inside the workspace**, including the `-Pcontainers` Testcontainers suite, through rootless podman and its Docker-compatible socket.
- **Edit Camel routes in Kaoto** and **use Claude Code**, both installed from open-vsx.org (neither exercised beyond installation; see below), and use `oc`, `tkn`, `tkn pac`, `gh`, JBang, Camel JBang and the `claude` CLI in the terminal.

Argo CD is still the only deployer to `<service>-dev`. None of the helpers write there.

| Item | Value |
|---|---|
| Platform | OpenShift 5.0.0-rc.7, single node; Dev Spaces `devspacesoperator.v3.29.1`; OpenShift Pipelines 1.24.3 (`tkn` 0.40.0, `tkn pac` 0.33.0) |
| Box1 UDI | New repository [box1-org/box1-devspaces](https://github.com/box1-org/box1-devspaces). Current image `box1-devtools/box1-udi@sha256:c3d29a29ae754af2544d052b87ec21d9ccea7dd5287a8cf4dc217d5512397310` (from `b784e8f`) |
| UDI contents | Base `registry.redhat.io/devspaces/udi-rhel9` pinned by digest. Adds JDK 21 as default, JBang 0.143.0 and `gh` 2.103.3 (both sha256-verified), Camel JBang 4.23.0, `claude-code` 2.1.319, and the `box1-pipeline`, `box1-remote-dev`, `box1-debug` and `box1-podman-socket` helpers |
| Extensions | `redhat.java`, `vscjava.vscode-java-debug`, `redhat.vscode-quarkus`, `redhat.vscode-kaoto`, `Anthropic.claude-code` from open-vsx.org |
| Sandbox | `mike-sandbox`, `edit` for `mike`, provisioned by box1-gitops `platform/dev-spaces/sandboxes/` |
| Runbook | [`runbooks/dev-spaces-developer-environment.md`](https://github.com/box1-org/box1-docs/blob/main/runbooks/dev-spaces-developer-environment.md) |

## Starting baseline

Recorded in #114 on 2026-11-08 before any change:

- No devfile or custom UDI existed in any box1-org repository. Workspaces got the stock UDI, editor and extension registry.
- The CheCluster set no `openVSXURL`. The embedded registry had Claude Code and the Java/Quarkus extensions but not Kaoto or Tekton.
- Container run was disabled in workspaces, so `podman run` and Testcontainers could not work.
- No JDWP configuration existed in any Box1 deployment.

## What changed

### Decisions (user, 2026-11-08)

- Pre-commit deploy uses **Quarkus remote dev** in a per-user sandbox, not `<service>-dev`.
- JVM debug is **always on in the sandbox** and **opt-in per service** in `<service>-dev`, through a kustomize component enabled by GitOps PR.
- JDWP binds to `127.0.0.1:5005` and is reached only through `oc port-forward`. It is set with `_JAVA_OPTIONS`, because Jib images start with a plain `java -jar` and services already use `JAVA_TOOL_OPTIONS`.
- **Kaoto is installed only.** Converting the fulfillment-adapter Java DSL routes was tracked separately in [#115](https://github.com/box1-org/box1-docs/issues/115), now closed.
- The **Tekton VS Code extension was dropped** mid-way. Tekton Hub is gone, and the extension depends on it. Pipelines run through `box1-pipeline` instead.

### Pull requests

| PR | Merge | Change |
|---|---|---|
| [box1-gitops#118](https://github.com/box1-org/box1-gitops/pull/118) | `791a9c4` | PaC `Repository` and `ci-udi-check`/`ci-udi-release` service accounts for box1-devspaces; `box1-devtools` image project with pull access for workspaces; CheCluster `openVSXURL: https://open-vsx.org`; `mike-sandbox` |
| [box1-devspaces#1](https://github.com/box1-org/box1-devspaces/pull/1) | `ad6020a` | UDI Containerfile, helpers, PR and release pipelines |
| [box1-devspaces#2](https://github.com/box1-org/box1-devspaces/pull/2) | `3303041` | `box1-pipeline validate` creates its own git-auth Secret, owned by the PipelineRun; adds `gh` |
| [box1-gitops#123](https://github.com/box1-org/box1-gitops/pull/123) | `24e4d6f` | Container run enabled with the built-in `nested-container` SCC (user namespaces, `/dev/fuse`, `/dev/net/tun`) |
| [box1-gitops#124](https://github.com/box1-org/box1-gitops/pull/124) | `845cd5c` | Container `runAsUser: 1000`, fixing the #123 regression below |
| [box1-gitops#125](https://github.com/box1-org/box1-gitops/pull/125) | `a1e1757` | Pod-level `runAsUser: 1000`, so `project-clone` writes `/projects` as the editor's UID |
| [box1-devspaces#3](https://github.com/box1-org/box1-devspaces/pull/3) | `7d4e7ba` | `box1-podman-socket`; `DOCKER_HOST` and `TESTCONTAINERS_RYUK_DISABLED=true` in the image |
| [box1-devspaces#4](https://github.com/box1-org/box1-devspaces/pull/4) | `b784e8f` | Podman storage moved to `/var/lib/box1-containers`, outside the persistent home |
| [fulfillment-adapter#9](https://github.com/box1-org/fulfillment-adapter/pull/9), [#11](https://github.com/box1-org/fulfillment-adapter/pull/11), [#12](https://github.com/box1-org/fulfillment-adapter/pull/12) | `e72d862`, `944b54d`, `f658258` | Pilot: devfile, `.vscode/`, `deploy/remote-dev/` with a throwaway PostgreSQL; Kafka input and SFTP disabled in the sandbox; Tekton extension dropped; podman socket from postStart; storage outside the home |
| [box1-templates#32](https://github.com/box1-org/box1-templates/pull/32) | `5663eb3` | The same files in the `quarkus-rest-service` skeleton, so new services get them |
| [box1-workloads-dev#179](https://github.com/box1-org/box1-workloads-dev/pull/179) | `84ec8ae` | `components/jvm-debug`: adds `_JAVA_OPTIONS` JDWP on `127.0.0.1:5005` and the pod annotation `box1.org/jvm-debug: enabled` |
| [box1-workloads-dev#185](https://github.com/box1-org/box1-workloads-dev/pull/185) | `a35c294` | Enables `jvm-debug` for inventory-service and order-service |
| 8 service PRs | see below | The pilot's setup copied to each service, with per-service sandbox PostgreSQL and Kafka isolation |
| [box1-docs#116](https://github.com/box1-org/box1-docs/pull/116), [#123](https://github.com/box1-org/box1-docs/pull/123) | `80debe2`, `a1d1f5b` | Runbook, then a refreshed status block |

The service PRs are [agentic-operations#7](https://github.com/box1-org/agentic-operations/pull/7) (`8ad728e`), [asset-service#7](https://github.com/box1-org/asset-service/pull/7) (`95bf5c8`), [inventory-service#6](https://github.com/box1-org/inventory-service/pull/6) (`2f37881`), [notification-service#6](https://github.com/box1-org/notification-service/pull/6) (`5151795`), [operations-console#16](https://github.com/box1-org/operations-console/pull/16) (`2a4035e`), [order-service#8](https://github.com/box1-org/order-service/pull/8) (`0bd686f`), [quarkus-reference#8](https://github.com/box1-org/quarkus-reference/pull/8) (`08dad41`) and [scenario-controller#5](https://github.com/box1-org/scenario-controller/pull/5) (`92d66b9`). The services that use JDBC get a sandbox PostgreSQL; those that use Kafka point it at an unreachable broker so the sandbox can't consume or publish shared events. Remote-dev readiness uses `/q/health/live`. legacy-erp and vm-golden-check were skipped: they are VM workloads.

UDI releases ran as `box1-ci` PipelineRuns `box1-udi-release-l5f8s` (`ba61eab4…`), `-vxs7t` (`08bc0b98…`), `-5mmqh` (`9ac4cffa…`) and `-6slvp` (`c3d29a29…`). Devfiles pin the image by digest, so moving to a new image is a reviewed bump in each repository.

**Made outside Git, with the user's approval in chat:** creating the public box1-devspaces repository; merges (most by the user); Argo syncs of `pipelines-ci`, `dev-spaces`, `inventory-service` and `order-service`; recreating the Dev Spaces dashboard pod; and the node-level unmounts described below.

## Incidents during rollout

- **Unsubstituted git-auth secret.** Run non-interactively, `tkn pac resolve` left `{{git_auth_secret}}` in place, and `fulfillment-adapter-validate-nrglm` failed with `PodCreationFailed`. Fixed in box1-devspaces#2.
- **No kubeconfig in the first workspace.** `oc whoami` returned the workspace service account (`ENOENT /home/user/.kube/config`). Recreating the dashboard pod and restarting the workspace fixed it. Root cause **not established**; the workaround is in the runbook.
- **#123 alone blocked every workspace start.** The SCC assigned UID 0, which conflicts with Dev Spaces' `runAsNonRoot` (`CreateContainerConfigError`). Fixed by #124. #125 then fixed `/projects` being cloned as root.
- **Workspace deletions stuck.** Two causes:
  - Rootless podman left sub-UID-owned layers on the per-user PVC that the cleanup job couldn't remove. They were cleared with `podman unshare` from an unprivileged helper pod.
  - Volumes mounted inside the persistent-home subPath (`.m2`, podman storage) made the kubelet's subPath unmount fail with `target is busy`, leaving `claim-devworkspace` Terminating and blocking the next workspace with "Shared PVC is in terminating state". Unmounting in the `oc debug` pod had no effect, because it has its own copy of the mount namespace. Unmounting the nested mounts in the host mount namespace (`nsenter -t 1 -m`) cleared it, three times, each approved by the user. The permanent fix is box1-devspaces#4 plus devfiles that mount nothing inside `/home/user`.
  - When a user's last workspace is deleted, the DevWorkspace operator deletes the per-user PVC by design, so the persistent home (including `~/.m2`) was lost once.
- **Dashboard WebSockets stuck "pending".** This was the browser's per-host connection limit: the router has HTTP/2 disabled. Closing tabs fixed it. Filed as wontfix [#119](https://github.com/box1-org/box1-docs/issues/119).

## Validation and evidence

Detailed evidence is in the #114 comments. Highlights:

| Check | Result |
|---|---|
| Toolchain | In a workspace on the Box1 UDI: `java -version` 21.0.12, `tkn` 0.40.0, `tkn pac` 0.33.0, `/etc/box1-udi-release` lists JBang, Camel JBang and claude-code; `gh` 2.103.3 |
| Extensions | All recommended extensions installed from open-vsx.org, including Kaoto 2.14.0 and Claude Code 2.1.319 |
| Tekton | `fulfillment-adapter-validate-jnsfx` ran for pushed HEAD `2736f1e` and Succeeded (Maven `BUILD SUCCESS` in 1:53); `box1-pipeline logs` streamed it to completion |
| Remote dev | Deploy took 82 s. An uncommitted `application.properties` edit appeared in `/q/openapi` on the sandbox Route after `sync`; `fulfillment-adapter-dev` was not touched |
| JVM debug, sandbox | JDWP listens only on `127.0.0.1:5005`; the handshake succeeds over port-forward; from another pod it is reset while HTTP 8080 returns 200 |
| JVM debug, `<svc>-dev` | inventory-service and order-service pods carry `box1.org/jvm-debug: enabled`; same positive and negative checks; **the user confirmed breakpoints hit from VS Code** |
| Nested containers | Pod admitted under `nested-container` with `hostUsers: false`; `podman run` reached `https://github.com`; a published PostgreSQL port was reachable |
| Testcontainers | fulfillment-adapter `-Pcontainers` through the podman socket: 130 tests, `BUILD SUCCESS` |

**Not tested or not established:**

- **Clean deletion with the fixed devfile.** Every workspace deleted so far either had the old mount layout (and needed the node unmount) or was deleted before the fix. Whether a workspace created from current `main` deletes on its own is **not verified**.
- **postStart socket start** in a fresh workspace: **not verified**; the socket was started by hand in testing.
- **Remote dev for the services other than fulfillment-adapter:** their devfiles pass the devfile 2.2.2 schema and their overlays build with kustomize, but **none has been run** in a workspace.
- **Claude Code sign-in:** **not tested**.
- **Kaoto in use:** the extension installed, but opening or editing a route in Kaoto is **not verified**. The #114 criterion "Kaoto opens a new `*.camel.yaml` file" is ticked, but no recorded evidence shows that check; treat it as unverified.
- **Vendor support:** whether the `nested-container` SCC with Dev Spaces 3.29.1 on OpenShift 5.0.0-rc.7 is supported is **not established**.

## Final operational state

Checked 2026-11-08 about 21:20 EST:

- **GitOps:** Argo apps `dev-spaces` and `pipelines-ci` are `Synced`/`Healthy` on box1-gitops `main` (`8e298a6`). `inventory-service`, `order-service` and `box1-workloads-dev` are `Synced`/`Healthy` at `937ccb3`. No manual overrides.
- **CheCluster:** `openVSXURL` open-vsx.org; container run enabled with the `nested-container` SCC, container and pod `runAsUser: 1000`, devices `/dev/fuse,/dev/net/tun`.
- **Images:** `box1-devtools/box1-udi` has tags for `ad6020a`, `3303041` and `b784e8f`. All devfiles on `main` pin `sha256:c3d29a29…`.
- **Workspaces:** `mike-devspaces` holds two stopped workspaces, `fulfillment-adapter` and `order-service`.
- **Sandbox:** `fulfillment-adapter-remote-dev` and its PostgreSQL are still running in `mike-sandbox` from testing. Remove them with `box1-remote-dev delete` when not needed.
- **Temporary state:** none. The node unmounts were one-off recoveries, not configuration.

## Recovery and follow-ups

- **Turn off debug in `<service>-dev`:** remove the `components:` block from the service's `kustomization.yaml` in box1-workloads-dev and sync.
- **Turn off nested containers:** revert box1-gitops #123–#125 and sync `dev-spaces`. Workspaces then fall back to no container run; `box1-podman-socket` fails harmlessly at postStart.
- **Return to an earlier UDI:** pin an earlier digest in the devfile. Each tagged image stays in `box1-devtools`.
- **Stuck workspace deletion:** follow the recovery steps in the runbook. None of the reverts above were exercised.
- **Open follow-ups:** [#120](https://github.com/box1-org/box1-docs/issues/120) (cleanup jobs vs pod-level UID), [#121](https://github.com/box1-org/box1-docs/issues/121) (Testcontainers in CI).
- **Related, closed:** [#124](https://github.com/box1-org/box1-docs/issues/124) confirmed Developer Hub rejects tokens signed with the operator's placeholder secret.
