# Dev Spaces developer environment

How to use the Box1 OpenShift Dev Spaces workspace. It covers running Tekton pipelines, editing Camel routes in Kaoto, using Claude Code, debugging JVMs, running uncommitted code on the cluster with Quarkus remote dev, and opening Hawtio. Tracking issue: [#114](https://github.com/box1-org/box1-docs/issues/114).

> **Status (2026-11-08, America/New_York): delivered.** [#114](https://github.com/box1-org/box1-docs/issues/114) is closed; the full record is the [achievement log](https://github.com/box1-org/box1-docs/blob/main/achievements/2026/2026-11-08-dev-spaces-developer-environment.md).
> - **In place:** the UDI (box1-devspaces, image `sha256:c3d29a29…`), the CheCluster, CI and sandbox changes in box1-gitops, Hawtio, the box1-templates skeleton and the Dev Spaces files in every service repository. JVM debug is enabled in `inventory-service-dev` and `order-service-dev`.
> - **Verified in a live `fulfillment-adapter` workspace:** the toolchain, the extensions from open-vsx.org, `oc` as the user, `box1-pipeline validate` and `logs`, remote-dev deploy and sync, nested podman and `-Pcontainers` through the podman socket, and a VS Code debugger attach to the sandbox and to `inventory-service-dev` and `order-service-dev`. JDWP refuses connections on the pod IP.
> - **Not verified:** Claude Code sign-in; opening or editing a route in Kaoto (only the extension install is recorded); remote dev for services other than `fulfillment-adapter`; the postStart event starting the podman socket on its own; and a workspace created from the current devfile deleting without help.
> - **Known problems:** workspace cleanup jobs are rejected when other workspaces exist ([#120](https://github.com/box1-org/box1-docs/issues/120)); `-Pcontainers` doesn't run in CI ([#121](https://github.com/box1-org/box1-docs/issues/121)).

## Pieces and where they live

| Piece | Repository / path | Managed by |
| --- | --- | --- |
| Box1 UDI image and the `box1-pipeline`, `box1-remote-dev`, `box1-debug` and `box1-podman-socket` helpers | [box1-devspaces](https://github.com/box1-org/box1-devspaces) `udi/` | PaC release builds the image on push to `main` → `box1-devtools/box1-udi` |
| PaC Repository, `ci-udi-*` service accounts, `box1-devtools` image project, workspace pull access | box1-gitops `platform/pipelines/ci/box1-devspaces.yaml` | Argo app `pipelines-ci` (manual sync) |
| CheCluster: `openVSXURL: https://open-vsx.org`, container run with the `nested-container` SCC, `runAsUser: 1000` | box1-gitops `platform/dev-spaces/instance/checluster.yaml` | Argo app `dev-spaces` (manual sync) |
| Per-user sandbox namespace `<user>-sandbox` | box1-gitops `platform/dev-spaces/sandboxes/` | Argo app `dev-spaces` |
| Opt-in JVM debug component (enabled for `inventory-service` and `order-service`) | box1-workloads-dev `components/jvm-debug` | Argo, per service |
| `devfile.yaml`, `.vscode/`, `deploy/remote-dev/` | box1-templates `quarkus-rest-service` skeleton, and every Java service repository (agentic-operations, asset-service, fulfillment-adapter, inventory-service, notification-service, operations-console, order-service, quarkus-reference, scenario-controller) | Each repository |
| Hawtio Online | box1-gitops `platform/hawtio/` | Argo apps (manual sync) |

The embedded Dev Spaces extension registry doesn't have Kaoto (`redhat.vscode-kaoto`), which is why the CheCluster uses open-vsx.org. The Tekton Pipelines extension was dropped on 2026-11-08: Tekton Hub is gone, and the extension is built around it. Run pipelines with the `box1-pipeline` commands below, which use `tkn` and `tkn pac` directly.

## Open a workspace

1. In Developer Hub, open the component and choose **Open in Dev Spaces**. Or go to `https://devspaces.apps.ocp.box1.org/#https://github.com/box1-org/<repo>`.
2. The workspace starts from the UDI image pinned by digest in `devfile.yaml`. It installs the extensions recommended in `.vscode/extensions.json`: Java, Java Debug, Quarkus, Kaoto and Claude Code.
3. Run commands from **Terminal → Run Task → devfile**, or run the `box1-*` helpers directly in a terminal.

Check the toolchain with `cat /etc/box1-udi-release`, `java -version` (expect 21), `tkn version`, `tkn pac version`, `camel --version` and `claude --version`.

**Run `oc whoami` first. It must print your OpenShift username.** The dashboard writes `~/.kube/config` with your token after the workspace starts. If the file is missing, `oc` falls back to the workspace service account and the `box1-*` helpers fail. On 2026-11-08 the first start from a factory link got no kubeconfig. Stopping and starting the workspace from the dashboard fixed it. The dashboard pod had also been recreated just before, so the cause isn't established. The dashboard logs only at ERROR level, so the injection step leaves no trace either way.

## Claude Code

The extension and the CLI are in every workspace. Never commit credentials. Pick one of these:

- **Interactive login:** sign in from the Claude Code panel.
- **API key:** create a Secret in your Dev Spaces namespace that is mounted as an environment variable in every workspace:

  ```bash
  oc create secret generic claude-api-key -n <user>-devspaces --from-literal=ANTHROPIC_API_KEY=<key>
  oc label secret claude-api-key -n <user>-devspaces controller.devfile.io/mount-to-devworkspace=true controller.devfile.io/watch-secret=true
  oc annotate secret claude-api-key -n <user>-devspaces controller.devfile.io/mount-as=env
  ```

  Restart the workspace to pick it up. Delete the Secret to revoke it.

## Tekton pipelines

| Command | Effect |
| --- | --- |
| `box1-pipeline validate` | Resolves `.tekton/pull-request.yaml` with `tkn pac resolve` for the **pushed** HEAD and creates the PipelineRun in `box1-ci`, plus a git-auth Secret owned by that run that's deleted when the run is pruned. It uses the GitHub token that Dev Spaces mounts, or `PAC_PROVIDER_TOKEN`. |
| `box1-pipeline logs` / `list` | Follows or lists this repository's PipelineRuns. |

- Pipelines fetch from GitHub, so uncommitted changes are never included. To try uncommitted code, use remote dev.
- Releases aren't started from the workspace. They run from Pipelines as Code on push to `main`, and Argo CD remains the only deployer.
- You need permission to create PipelineRuns and Secrets in `box1-ci`, which is limited to maintainers.

## Remote dev: uncommitted code on the cluster

```bash
box1-remote-dev deploy   # mutable-jar image -> <user>-sandbox, applies deploy/remote-dev
box1-remote-dev sync     # quarkus:remote-dev: pushes local changes as you save
box1-remote-dev url      # sandbox Route
box1-remote-dev delete   # removes the remote-dev resources, live-reload Secret and ImageStream
```

- Jib pushes the image to `registry.apps.ocp.box1.org/<user>-sandbox/<service>:remote-dev` using your own token. Nothing goes to `box1-ci`, and `<service>-dev` isn't touched.
- The pod runs with `QUARKUS_LAUNCH_DEVMODE=true`. The live-reload password is a random value in the Secret `<service>-remote-dev-live-reload`.
- **Deliberate difference from dev:** the root filesystem is writable, because remote dev rewrites the application jars in place.
- Services with dependencies isolate them in their overlay. `fulfillment-adapter` runs a throwaway PostgreSQL (`emptyDir`, deleted along with the rest), disables Kafka input and uses an unreachable broker so it never takes orders from `fulfillment-adapter-dev` or publishes into shared topics, and leaves SFTP disabled.
- To add a developer, copy `platform/dev-spaces/sandboxes/mike.yaml` in box1-gitops and sync `dev-spaces`.

## JVM debugging

JDWP always listens on `127.0.0.1:5005` inside the pod, so other pods and the mesh can't reach it. You attach only through `oc port-forward`.

| Target | Steps |
| --- | --- |
| Workspace `quarkus:dev` | Run the **Quarkus dev** task, then start **Attach to JVM (localhost:5005)**. |
| Sandbox remote-dev pod | Run `box1-debug sandbox`, then attach. |
| `<service>-dev` | Open a box1-workloads-dev PR adding `components: [../../components/jvm-debug]` to `workloads/<service>/kustomization.yaml` and sync. Then run `box1-debug dev <service>` and attach. Remove the component when you no longer need it. `inventory-service` and `order-service` keep it enabled on purpose (box1-workloads-dev#185). |

A paused breakpoint stops request handling and can fail probes, so expect restarts during long pauses. Only one forward can use local port 5005 at a time. Set `BOX1_DEBUG_PORT` to use another port, and change `launch.json` to match.

## Kaoto

Kaoto opens Camel YAML/XML routes. `fulfillment-adapter`'s routes were converted to the YAML DSL in fulfillment-adapter#10 ([#115](https://github.com/box1-org/box1-docs/issues/115)) and live in `src/main/resources/routes/*.camel.yaml` (`erp1-exchange`, `fulfillment`, `rest-api`). Open one of those files to edit it in Kaoto. Use `camel run <file>.camel.yaml` (Camel JBang) to try a route on its own.

Using Kaoto inside a workspace hasn't been verified yet: only the extension install is recorded.

## Hawtio

The **Hawtio** devfile task prints the Hawtio Online URL from the `hawtio` namespace. Pods show up there when they expose a `jolokia` port. `fulfillment-adapter` is the first service set up for this (box1-gitops#117, fulfillment-adapter#8, box1-workloads-dev#178).

## Containers in workspaces

Since box1-gitops#123, the CheCluster runs workspaces with container run enabled. It uses the built-in `nested-container` SCC, gives each workspace pod its own user namespace, and adds `/dev/fuse` and `/dev/net/tun`. Podman stores images in `/var/lib/box1-containers` (the UDI sets `CONTAINERS_STORAGE_CONF`), and Box1 devfiles mount an ephemeral volume there, so images and containers are discarded when the workspace stops. **Don't mount volumes inside `/home/user`.** It's the persistent home, a subPath of the per-user PVC, and mounts nested inside it block workspace deletion (see the recovery below). `~/.m2` persists with the home and needs no volume of its own.

Workspace containers run as UID 1000. Both levels are set in the CheCluster: `containerRunConfiguration.containerSecurityContext.runAsUser` (box1-gitops#124) and `security.podSecurityContext.runAsUser` (box1-gitops#125). Without them, `nested-container` assigns UID 0, which either fails the start or leaves `/projects` owned by root.

### Testcontainers (`-Pcontainers`)

- A devfile postStart event runs `box1-podman-socket start`, which serves podman's Docker API at `/tmp/podman-run/podman.sock`.
- The UDI sets `DOCKER_HOST` to that socket and `TESTCONTAINERS_RYUK_DISABLED=true`, so `./mvnw -Pcontainers test` works with no extra setup.
- Check it with `box1-podman-socket status`.
- **Verified by hand on 2026-11-08:** fulfillment-adapter ran 130 tests, `BUILD SUCCESS`, with `postgres:15-alpine` and `apache/kafka:4.2.0`.
- Images come from docker.io, which applies anonymous pull rate limits. `registry.redhat.io` images need pull credentials, which workspaces don't have.

### Recovery: workspace deletion stuck on podman storage

**Symptom:** the `cleanup-<workspace-id>` job in `<user>-devspaces` fails with `rm: cannot remove '…/persistent-home/.local/share/containers/storage/vfs/dir/…': Operation not permitted`, and the DevWorkspace stays in Error with a deletion timestamp. This happens when a workspace ran podman before the ephemeral volume was added. Image layers end up on the per-user PVC owned by sub-UIDs (for postgres, host UID 10069 = container UID 70), and the cleanup job runs as the plain user UID.

**Fix without a privileged pod** (used on 2026-11-08):
1. Start a pod in `<user>-devspaces` that matches the old workspace:
   - Use the workspace's `workspace<id>-sa` service account, which may still use `container-build`.
   - Set the annotation `openshift.io/required-scc: container-build`.
   - Use the Box1 UDI image.
   - Give the container `allowPrivilegeEscalation: true` and add SETGID and SETUID.
   - Mount `claim-devworkspace` with `subPath: workspace<id>/persistent-home` at `/home/user`.
2. In that pod, add `user:x:$(id -u):0:user:/home/user:/bin/bash` to `/etc/passwd`, so the image's `/etc/subuid` entry `user:10000:65536` applies.
3. Set `P="/usr/bin/podman.orig --storage-driver=vfs --root /tmp/ps-root --runroot /tmp/ps-run"`.
4. For each `…/vfs/dir/*/var/lib/postgresql`, run `$P unshare sh -c 'cd <dir> && setpriv --reuid=70 --regid=70 --clear-groups rmdir data'`. User-namespace root can't remove these sticky directories because their group isn't mapped.
5. Run `$P unshare rm -rf /home/user/.local/share/containers/storage`.
6. Delete the helper pod and the failed `cleanup-<workspace-id>` job. The DevWorkspace controller recreates the job, and the deletion completes.

### Recovery: workspace pod stuck terminating, per-user PVC stuck Terminating

**Symptom:**
- A new workspace stops at "Provisioning storage: Shared PVC is in terminating state" and fails after 5 minutes.
- The old workspace pod stays in `Error` with a deletion timestamp.
- The kubelet log shows `umount: …/volume-subpaths/pvc-…/<container>/<n>: target is busy` every 2 minutes.

**Cause (2026-11-08):** devfile volumes mounted at `/home/user/.m2` and `/home/user/.local/share/containers` stayed mounted on the node, inside each container's subPath of the persistent home.

**Fix:**
1. List the nested mounts: `oc debug node/<node> -- chroot /host findmnt -R <busy subPath>`.
2. Unmount them **in the host mount namespace**: `oc debug node/<node> -- chroot /host nsenter -t 1 -m -- umount <mount>`, deepest first. A plain `umount` inside `oc debug` only affects the debug pod's own copy of the mount namespace.

The kubelet then finishes deleting the pod within about a minute, the old PVC and PV are deleted, and the next workspace start creates a new PVC. Since box1-devspaces#4 nothing is mounted inside the home, so this shouldn't recur.

### Known problem: deletion stuck on "Cleaning up resources for deletion"

If you delete a workspace while you still have others, its `cleanup-<workspace-id>` job can fail with `FailedCreate … restricted-v2: … runAsUser: Invalid value: 1000`. The pod-level `runAsUser: 1000` from box1-gitops#125 also applies to cleanup jobs, which `restricted-v2` rejects. There is no config fix yet ([#120](https://github.com/box1-org/box1-docs/issues/120)). To work around it, either delete your other workspaces too, which lets the operator remove the whole per-user PVC, or remove the workspace's directory from the PVC with a helper pod as described in the podman-storage recovery above.

**Also expected:** when you delete your last workspace, the DevWorkspace operator deletes the per-user `claim-devworkspace`, and the persistent home (including `~/.m2`) goes with it.

## Updating the UDI

1. Change `udi/Containerfile` or `udi/bin` in box1-devspaces with a PR. The PR pipeline builds the image without pushing.
2. When the PR merges, the release run prints `…/box1-devtools/box1-udi@sha256:…`.
3. Bump that digest in the template `devfile.yaml` and in each repository that uses it.
4. When Dev Spaces is upgraded, bump `BASE_IMAGE`. The command for finding the new digest is in the Containerfile header.

## Recovery

| To undo | Do this |
| --- | --- |
| A repository's devfile | Revert its `devfile.yaml` and `.vscode/` files. Without a devfile, workspaces fall back to the operator defaults. |
| The open-vsx.org registry | Revert the `openVSXURL` line and sync `dev-spaces`. Kaoto then stops installing. |
| A sandbox | Run `box1-remote-dev delete`. Removing its file from `sandboxes/` and syncing deletes the namespace. |
| JVM debug on a dev service | Remove the component and sync. |
| Containers in workspaces | Revert box1-gitops #123, #124 and #125 and sync `dev-spaces`. Workspaces lose podman and Testcontainers; `box1-podman-socket` fails harmlessly at postStart. |
| A UDI release | Pin an earlier digest in `devfile.yaml`. Every released image stays tagged in `box1-devtools`. |

None of these recovery steps has been exercised yet. The two stuck-deletion recoveries above were used on 2026-11-08.

## Related PRs

- UDI: [box1-devspaces#1](https://github.com/box1-org/box1-devspaces/pull/1) (image, helpers, pipelines), [#2](https://github.com/box1-org/box1-devspaces/pull/2) (pipeline git-auth, `gh`), [#3](https://github.com/box1-org/box1-devspaces/pull/3) (podman socket), [#4](https://github.com/box1-org/box1-devspaces/pull/4) (storage outside the home)
- GitOps: [box1-gitops#118](https://github.com/box1-org/box1-gitops/pull/118) (UDI build and pull, open-vsx.org, sandbox), [#123](https://github.com/box1-org/box1-gitops/pull/123), [#124](https://github.com/box1-org/box1-gitops/pull/124), [#125](https://github.com/box1-org/box1-gitops/pull/125) (containers in workspaces)
- JVM debug: [box1-workloads-dev#179](https://github.com/box1-org/box1-workloads-dev/pull/179) (component), [#185](https://github.com/box1-org/box1-workloads-dev/pull/185) (inventory-service, order-service)
- Devfiles: [box1-templates#32](https://github.com/box1-org/box1-templates/pull/32) (skeleton); pilot [fulfillment-adapter#9](https://github.com/box1-org/fulfillment-adapter/pull/9), [#11](https://github.com/box1-org/fulfillment-adapter/pull/11), [#12](https://github.com/box1-org/fulfillment-adapter/pull/12); and one PR per service ([agentic-operations#7](https://github.com/box1-org/agentic-operations/pull/7), [asset-service#7](https://github.com/box1-org/asset-service/pull/7), [inventory-service#6](https://github.com/box1-org/inventory-service/pull/6), [notification-service#6](https://github.com/box1-org/notification-service/pull/6), [operations-console#16](https://github.com/box1-org/operations-console/pull/16), [order-service#8](https://github.com/box1-org/order-service/pull/8), [quarkus-reference#8](https://github.com/box1-org/quarkus-reference/pull/8), [scenario-controller#5](https://github.com/box1-org/scenario-controller/pull/5))
- Hawtio: [box1-gitops#117](https://github.com/box1-org/box1-gitops/pull/117), [fulfillment-adapter#8](https://github.com/box1-org/fulfillment-adapter/pull/8), [box1-workloads-dev#178](https://github.com/box1-org/box1-workloads-dev/pull/178)
