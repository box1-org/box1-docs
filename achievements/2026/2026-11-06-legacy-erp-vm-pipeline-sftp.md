# Legacy ERP VM: one pipeline for two repositories, SFTP exchange with the adapter, console redraw

**Date:** 2026-11-05 about 22:30 EST to 2026-11-06 about 13:15 EST (America/New_York)
**Status:** Delivered and verified on the cluster. [box1-docs#25](https://github.com/box1-org/box1-docs/issues/25) stays open: 3 of its 10 acceptance boxes are ticked, each with its proof level stated in an issue comment.

**Background:**
- [Legacy ERP appliance](2026-11-05-legacy-erp-appliance.md): the application and its file protocol.
- [RHEL image mode VM golden path](2026-11-05-rhdh-vm-golden-path.md): the VM, the bootc build and the promotion flow.
- [Fulfillment adapter delivery](2026-11-05-fulfillment-adapter-delivery.md): the modern side of the exchange.

## Outcome

The `legacy-erp` VM now runs the Python ERP as a RHEL 10 image mode appliance. It boots straight into the ERP console on the serial port, and its ledger lives on a data disk of its own.

**One pipeline builds and deploys it.** A merge to `main` in either repository starts the same pipeline:
- [box1-org/legacy-erp](https://github.com/box1-org/legacy-erp) holds the OS image;
- [box1-org/box1-ops-erp-simulator](https://github.com/box1-org/box1-ops-erp-simulator) holds the ERP code.

The pipeline:
1. builds the ERP from source into the bootc image;
2. scans it;
3. promotes it through GitOps;
4. applies it to the running VM over SSH;
5. proves the VM booted the exact digest it built.

No manual step remains between a merge and a running VM.

**The ERP and the fulfillment adapter exchange files over SFTP.** A real fulfillment went through the full round trip on 2026-11-06:
1. The adapter's REST API accepted it.
2. The adapter uploaded the request file to the VM.
3. An operator shipped it in the ERP console.
4. The adapter consumed the result file.
5. The adapter published `shipment.confirmed.v1` to Kafka.

This is the first time the legacy and modern halves of the demonstration have talked to each other.

**The console can repair its own screen.** Ctrl-L, or `G` on the request list, resets the terminal and redraws every cell. This is for a serial console garbled by line noise, or left blank after a `virtctl console` reconnect.

## Starting baseline

As of 2026-11-05, before this work:

- **No ERP in the VM.** The golden-path VM `legacy-erp` (namespace `legacy-erp-dev`) booted a plain image built from `legacy-erp`. It had no ERP, no data disk and no ERP units.
- **ERP shipped as a bundle only.** The ERP existed as a separate artifact: a one-layer bundle image, `box1-ci/box1-ops-erp-simulator@sha256:34053e1b…aab`.
- **Deploys were manual.** The golden-path pipeline stopped after `box1-bootc-channel` moved the `development` tag. Applying an image to the guest was a manual `bootc upgrade --apply` (`box1-vm-smoke` printed that instruction).
- **SFTP was off.** The adapter was live in `fulfillment-adapter-dev` with `FULFILLMENT_SFTP_ENABLED=false`, because no SFTP endpoint existed. Requests accepted through its API stayed queued, among them `ful_demo1`, accepted 2026-11-05 21:42 EST.
- **No redraw key.** The console had none. `G` only set a "Refreshed." message.

## What changed

| Repository | PR | Merge | Change |
|---|---|---|---|
| `box1-gitops` | [#72](https://github.com/box1-org/box1-gitops/pull/72) | `5e05888` | `box1-bootc-build` gains optional `extra-source-*` parameters to fetch a second repository into the build context. New task `box1-bootc-apply`. ServiceAccount `ci-vm-deploy`. The simulator's Pipelines as Code token is scoped to `legacy-erp` and `box1-workloads-dev` |
| `box1-workloads-dev` | [#80](https://github.com/box1-org/box1-workloads-dev/pull/80) | `d66295d` | PVC `legacy-erp-data` (2 Gi, Block, `Prune=false,Delete=false`) attached as disk serial `erpdata`. Deploy public key delivered through KubeVirt `accessCredentials` for user `box1-deploy`. A Role letting `ci-vm-deploy` `get` this VMI and use its `portforward` subresource, and nothing else |
| `legacy-erp` | [#2](https://github.com/box1-org/legacy-erp/pull/2) | `20a88f8` | Multi-stage Containerfile: builds the ERP wheel from `erp-src/` and installs it per the simulator's `docs/VM-INTEGRATION.md`. Units, default target `box1-erp.target`, data-disk format and provision services, restricted `box1-deploy` user, and the shared pipeline `.tekton/appliance-pipeline.yaml` |
| `legacy-erp` | [#3](https://github.com/box1-org/legacy-erp/pull/3) | `27a2922` | XFS label `box1erpdata`. The 13-character label was rejected (limit 12) |
| `box1-gitops` | [#74](https://github.com/box1-org/box1-gitops/pull/74) | `4368557` | `box1-bootc-apply` stops treating the session dropped by the guest's reboot as a failure (see Validation) |
| `legacy-erp` | [#5](https://github.com/box1-org/legacy-erp/pull/5) | `6deff70` | The ERP venv `bin/` is labelled `bin_t`. Without it the units stayed in `init_t` and could not write the ledger lock |
| `legacy-erp` | [#6](https://github.com/box1-org/legacy-erp/pull/6) | `8447cb9` | All SELinux changes in one `semanage import`. Two `semanage` commits in one buildah `RUN` failed with "Directory not empty" |
| `box1-ops-erp-simulator` | [#4](https://github.com/box1-org/box1-ops-erp-simulator/pull/4) | `7b13529` | The simulator's release trigger runs legacy-erp's pipeline: the remote-pipeline annotation pointing at `legacy-erp` `main`, with `erp-revision` set to the pushed commit |
| `legacy-erp` | [#7](https://github.com/box1-org/legacy-erp/pull/7) | `169248f` | The SFTP endpoint (details below) |
| `box1-workloads-dev` | [#100](https://github.com/box1-org/box1-workloads-dev/pull/100) | `a5e472c` | Service `legacy-erp-sftp` (22 → 2222) and NetworkPolicy `legacy-erp-sftp`. The adapter gets `FULFILLMENT_SFTP_ENABLED=true` and host `legacy-erp-sftp.legacy-erp-dev.svc:22` |
| `box1-workloads-dev` | [#102](https://github.com/box1-org/box1-workloads-dev/pull/102) | `e6e7e44` | The NetworkPolicy also allows TCP 22, which #100 had blocked (see Validation) |
| `box1-ops-erp-simulator` | [#5](https://github.com/box1-org/box1-ops-erp-simulator/pull/5) | `c82d318` | Console Ctrl-L / `G` full redraw, with a pty regression test |

The user merged every PR except the pipeline's own promotion PRs.

**Single pipeline (decisions).**
- **Pipeline location.** The Pipeline `legacy-erp-appliance` lives in `legacy-erp/.tekton/`. Each repository has a thin `release.yaml` that names it as a remote pipeline and sets the revisions:
  - a legacy-erp push builds with simulator `main`;
  - a simulator push builds with legacy-erp `main`.
  
  With PaC's `default_branch` provenance, both use the definitions on `main`.
- **Task order:** `resolve`, `erp-test`, `build`, `security`, `disk`, `current`, `promote`, `channel`, `deploy`, `smoke`.
- **ERP source is built in the image.** It is built from source in the image build stage (`SOURCE_DATE_EPOCH` fixed), not copied from the bundle image. The image records both revisions: labels `org.box1.erp.revision`, and `REVISION` and `ERP_REVISION` in `/usr/lib/box1-image-release`.
- **Deploy over SSH.** The deploy goes through `virtctl ssh` to the restricted `box1-deploy` user, whose sudoers allow exactly two commands:
  - `bootc upgrade --apply`;
  - `bootc status --format json`.
  
  The task then waits until:
  - the guest reports the built digest as booted;
  - `box1-erp.target` is the default;
  - `box1-erp-worker`, `box1-erp-tui@ttyS0` and `box1-erp-sftpd` are active.
- **Deploy credential.** The private key is Secret `box1-ci/legacy-erp-deploy-ssh`, created by the user outside Git. Guest host keys are accepted on first use and printed (follow-up below).

**Data disk.** `/var/srv/box1-erp` is mounted from `/dev/disk/by-id/virtio-erpdata`. (`/srv` is a symlink to `var/srv`, so the mount unit is `var-srv-box1\x2derp.mount`.)
- **Formatting is guarded.** `format-data-disk` formats only a disk with no signature whose first MiB is zeros.
- **The ledger is created at most once.** `provision-data` runs the simulator's `provision-data-volume.sh` and adds `--init-ledger` only when the marker `.box1-initialized` is absent.
- **No data volume, no ERP.** The worker, console and sftpd all require the mount and the provision service.

**SFTP endpoint.** A second sshd, `box1-erp-sftpd.service`, listens on port 2222 with `/etc/ssh/sshd_config.box1-sftp`:
- only `erpsftp`, by public key only;
- `ForceCommand internal-sftp -u 0007`, chrooted to `/var/srv/box1-erp/exchange`;
- no TTY and no forwarding.

How the pieces fit:
- **Admin SSH refuses the SFTP account.** The admin sshd on port 22 carries `DenyUsers erpsftp`, and does not depend on the data disk, so admin recovery still works without it.
- **Stable host key.** The SFTP host key is generated once on the data volume (`ssh/ssh_host_ed25519_key`, labelled `sshd_key_t`), so it survives OS updates and guest rebuilds.
- **Adapter key.** The adapter's public key is baked into the image at `/etc/ssh/authorized_keys/erpsftp`. Its private key and `known_hosts` are in Secret `fulfillment-adapter-dev/fulfillment-adapter-sftp`, created on the cluster with the user's approval and not in Git. The local copies of the private keys were deleted.
- **SELinux changes, in one transaction:**
  - port 2222 as `ssh_port_t`;
  - the `sshd_key_t` file context;
  - the venv `bin_t` context;
  - boolean `virt_qemu_ga_manage_ssh`.
- **Network.** The NetworkPolicy allows TCP 2222 only from pods `app.kubernetes.io/name=fulfillment-adapter` in `fulfillment-adapter-dev`. The adapter stays cross-namespace; moving it is [#52](https://github.com/box1-org/box1-docs/issues/52).

**Console redraw.**
- `Tui.getkey()` handles Ctrl-L, so it works on every screen and inside prompts.
- `repaint()` runs `endwin()` + `refresh()`, which re-sends the terminal init strings and restores raw and keypad modes.
- It then re-reads the size and redraws with `clearok()`.
- The help screen and `docs/RUNBOOK.md` document it.

## Validation and evidence

**Pipeline runs** (PipelineRuns in `box1-ci`, all times EST):

| Run | Trigger | Result |
|---|---|---|
| `legacy-erp-release-7shqj` | legacy-erp `20a88f8` | Failed at `deploy`. The old image had no `box1-deploy` user, so the first move to the ERP image was a one-time manual `bootc upgrade --apply` as `cloud-user`. The ERP units then stayed inactive because the data disk could not be formatted (label too long → #3) |
| `legacy-erp-release-z2hfj` | `27a2922` | Failed at `promote`. The promotion PR's `box1-phase1-smoke` check was stranded by the PaC check-run 404 ([#64](https://github.com/box1-org/box1-docs/issues/64#issuecomment-6678777713)) |
| `legacy-erp-release-nrbhc` | `d7eb309` | The guest booted the new image, but `deploy` failed. After the reboot `virtctl ssh` exits 1, not 255 → #74. The guest showed the worker denied writing `ledger.lock` (`init_t` → `var_t`) → #5 |
| `legacy-erp-release-8q7lz` | `6deff70` | Failed at `build`: `semanage` rename "Directory not empty" → #6 |
| `legacy-erp-release-k8whl` | `8447cb9`, 00:05 EST | **Succeeded**, all 10 tasks. Booted digest = built `sha256:228d3ac0…8889`, `smoke` PASS. *Proves the legacy-erp trigger path* |
| `box1-ops-erp-simulator-release-jlq92` | simulator `7b13529`, 00:21 EST | **Succeeded**, same pipeline, with `erp-revision=7b13529`. *Proves the simulator trigger path* |
| `legacy-erp-release-ghvjz` | `169248f` (SFTP), 00:56 EST | **Succeeded**. Booted `sha256:a39932fe…984b` with `box1-erp-sftpd` active |
| `box1-ops-erp-simulator-release-bgnlm` | simulator `c82d318` (Ctrl-L), 12:46 EST | **Succeeded**. Booted `sha256:71bbe4a1…aed6`, promotion [#109](https://github.com/box1-org/box1-workloads-dev/pull/109). The first deploy through the corrected NetworkPolicy |

`box1-bootc-apply` decides success only on the booted digest, the default target and the unit states, not on the SSH session's exit code. The full images, SBOMs and scan results are linked from each run's results (RHACS and RHTPA URLs).

**In the guest** (admin SSH, read-only):
- SELinux is Enforcing with 0 AVC denials since boot.
- The default target is `box1-erp.target`.
- sshd is listening on 22 and on 2222.
- The SFTP host key on the volume is labelled `sshd_key_t`.
- `DenyUsers erpsftp` is in effect on port 22.
- The ledger marker was written 2026-11-05 23:49:42 EST and has been kept across every later image update.
- Since the last boot, sftpd logged 22 accepted public-key logins for `erpsftp`.

**User observation:** the ERP console is usable through `virtctl console` (#25 boxes "default target" and "console path" were ticked on that basis).

**End-to-end exchange** (`ful_demo1` / `ord_demo1`; [evidence comment](https://github.com/box1-org/box1-docs/issues/25#issuecomment-6692075346)):

| Step | Observed (EST) |
|---|---|
| Upload | The queued request was uploaded to `inbound/` at 01:10:57 once SFTP was enabled. The ERP's PENDING result (revision 1) was applied one second later |
| Ship | The user shipped it in the console. The ERP wrote `RES.ful_demo1.000002…` at 13:14:25 |
| Consume | The adapter applied `SHIPPED` revision 2 at 13:14:26 and moved every result file to `consumed/`. `inbound/` and `outbound/` are empty |
| API | `GET /api/fulfillments/ful_demo1` returns `outcome=SHIPPED`, `revision=2`, `shipmentId=shp_c394c398b78de9abcb780068abb05b26` |
| Event | `box1.fulfillment.events.v1` holds `shipment.confirmed.v1`, event `6acdda5b-284c-4d72-b096-cee4d31eecae`, with the same shipment and order. Outbox published 1, lag 0.137 s, 0 pending |

**Other observations:**
- The adapter's status probes made the ERP re-send revision 1 three times; each was ignored as a duplicate, as designed.
- The VM reboot during the 12:5x deploy refused SFTP briefly. The adapter reconnected without intervention.

**Console redraw:**
- **Local test.** New pty + pyte test at 80x24 / `vt100`. It garbles the emulated screen without the TUI knowing, checks that an ordinary refresh does not repair it, then checks that Ctrl-L (list, Find prompt, detail) and `G` do. It fails on the previous code. Full suite 155 passed (local, Python 3.14).
- **On the VM.** `virtctl console`, driven through a pty and an emulator, with only Ctrl-L sent. On connect the screen was blank; the console was at its operator-label prompt and had nothing new to send. Ctrl-L redrew the prompt. After the local copy was garbled, a second Ctrl-L cleared it. Only that prompt screen was exercised on the VM.

**Failure found during the work and fixed.** After #100 synced, `virtctl ssh` timed out ("Connection timed out during banner exchange"). virtctl's port-forward reaches the guest's port 22 as ordinary pod ingress, and the new policy allowed only 2222. Until #102, admin SSH and every pipeline deploy were blocked; SFTP and the ERP were unaffected. After #102 synced (12:50 EST), admin SSH worked and run `…-bgnlm` deployed through the policy.

**Not tested / not established:**
- **SFTP refusals on the cluster:** no shell, wrong user, unknown key, no access outside the exchange directories. They passed only in the simulator's local container harness (2026-11-05 log).
- **Policy denial.** The NetworkPolicy refusing 2222 from another namespace needs a test pod and the user's approval.
- **Hold → release** in the console.
- **Cold boot, restarts and recovery:** cold boot to the console; worker and console recovering independently; restart rate limits; the `serial-getty` fallback.
- **Storage:** reboot plus guest-disk replacement with the data disk kept; a missing data disk at boot; backup and restore.
- **Console screens:** every screen other than the label prompt over the real serial console.
- **Rollback:** `bootc rollback` and the Git revert paths below were not exercised.

## Final operational state

- **VM.** `legacy-erp-dev/legacy-erp` boots `box1-ci/legacy-erp:development` = `sha256:71bbe4a18875dff5f610f7a775a42e60d82eb67c2895ab3769ebe1c68c8eaed6`, built from legacy-erp `169248f` and simulator `c82d318`. It is tracked by `bootc` and updated only through the pipeline's `deploy` step.
- **Kubernetes objects** are managed by Argo CD from `box1-workloads-dev` (`workloads/legacy-erp/`, synced at `ec52fb4` after promotion #109):
  - the VM;
  - the data PVC;
  - the deploy access Role and key;
  - the SFTP Service and NetworkPolicy;
  - the adapter Deployment.
- **Pipelines.** Pipeline definitions are in `legacy-erp/.tekton/` (Pipelines as Code, from `main`), and the shared tasks in `box1-gitops` `platform/pipelines/tasks/`.
- **Outside Git:**
  - Secret `box1-ci/legacy-erp-deploy-ssh`, created by the user;
  - Secret `fulfillment-adapter-dev/fulfillment-adapter-sftp`, labelled `box1.org/purpose=erp-sftp`.
  
  Rebuilding the cluster from Git does not recreate them.
- **NetworkPolicy `legacy-erp-sftp`:**
  - TCP 2222 only from the adapter pods;
  - TCP 22 from any source. This restores the pre-policy reach of the admin sshd, which is key-only.
- **No temporary workarounds** are in place. The one manual `bootc upgrade` was a one-time bootstrap; every later image arrived through the pipeline.

## Recovery and follow-ups

**Recovery** (none of these were exercised):
- **OS image.** Run `sudo bootc rollback` as admin and reboot to return to the previous image. The data disk is unaffected.
- **Stop the exchange.** Set `FULFILLMENT_SFTP_ENABLED=false` in `box1-workloads-dev` `workloads/fulfillment-adapter/deployment.yaml`. The adapter queues requests again until it is re-enabled.
- **Remove the endpoint.** Revert #100 / #102; the Service and NetworkPolicy are pruned.
- **Data disk.** The PVC is annotated `Prune=false,Delete=false`, so removing it from Git does not delete it. The ERP runbook covers backup, restore and guest rebuild.
- **Garbled console.** Ctrl-L, or as admin `systemctl restart box1-erp-tui@ttyS0` (the worker is unaffected).

**Follow-ups:**
- **[#25](https://github.com/box1-org/box1-docs/issues/25) remaining boxes:**
  - cold boot;
  - 80x24 and reconnect across all screens;
  - independent recovery;
  - networking, SFTP and administrative recovery (the negative checks);
  - persistence through reboot and guest replacement;
  - missing storage;
  - backup/restore and the demonstration.
- **[#13](https://github.com/box1-org/box1-docs/issues/13) and [#14](https://github.com/box1-org/box1-docs/issues/14):** their VM-dependent criteria can now be judged against the evidence above. They have not been updated yet.
- **[#64](https://github.com/box1-org/box1-docs/issues/64):** the PaC check-run 404 strands checks. A `/retest <name>` posted as a **PR** comment recovers; posted on a commit it fails.
- **[#52](https://github.com/box1-org/box1-docs/issues/52):** adapter and ERP in one namespace.
- **[#75](https://github.com/box1-org/box1-docs/issues/75):** pin guest host keys in `box1-bootc-apply` instead of trusting on first use, and make the admin sshd host key durable across guest rebuild.
- **[#76](https://github.com/box1-org/box1-docs/issues/76):** retire the now-unused simulator bundle ImageStream and the `ci-erp-release` RBAC.
- **Housekeeping:** close the unneeded re-trigger PR [legacy-erp#4](https://github.com/box1-org/legacy-erp/pull/4).
- **Cluster cleanup.** The orphan PipelineRun `box1-phase1-smoke-kf7kf` left by #64 is for the user to delete; the agent's attempt was refused.
