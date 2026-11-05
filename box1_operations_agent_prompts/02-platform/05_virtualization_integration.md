# Platform 05 — Virtualization: boot-to-TUI legacy ERP appliance


> **Platform workstream, not a new microservice.** Keep the existing box1 Golden Path, pipelines/GitOps and cluster infrastructure intact. Inspect live cluster/operator support and GitOps repo before writing any CRs. Under the `qwen-64k` profile these prompts target a nominal **64K total context window**; load one workstream at a time. Read `00-shared/00_AGENT_CONTRACT.md`, `01_DOMAIN_CONTRACTS.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`. Backlog: [box1-docs#25](https://github.com/box1-org/box1-docs/issues/25).

**Safety:** No direct operator installation, secret creation, destructive migration, or privileged cluster mutation without explicit authorization. Prefer a reviewed declarative GitOps PR. Treat prerelease OpenShift/operator compatibility as unverified until inspected. SNO does not provide node-level HA or live migration.

**Requirements:** VM-01–06; NFR-04; DEMO-C1/C2

**Dependencies:** the Python ERP application and its systemd units from `01-services/04_erp_vm_simulator.md` ([#14](https://github.com/box1-org/box1-docs/issues/14)); the adapter in `01-services/03_fulfillment_adapter.md` ([#13](https://github.com/box1-org/box1-docs/issues/13)); a healthy OpenShift Virtualization installation.

## Mission

The ERP VM is a required part of the demonstration, not an alternative location for an HTTP service. Provision a Linux VM that boots directly into the Python ERP console from #14; the adapter from #13 reaches its SFTP endpoint. There are **no ERP HTTP endpoints, HTTP readiness checks or ERP Route**.

**#25 owns** the provisioned VM, default boot target, console binding, storage, networking, access controls and end-to-end appliance validation. **#14 owns** the application, TUI, worker and application units. **#13 owns** the Camel routes and the modern boundary.

## Implementation scope and guardrails

- **Boot.** Install and select `box1-erp.target` (`systemctl set-default box1-erp.target`). It keeps the normal multi-user environment, starts the worker and the TUI on the selected console, and retains networking and administrative SSH. Starting structure: `Requires=multi-user.target`, `After=multi-user.target`, `Wants=box1-erp-worker.service box1-erp-tui@ttyS0.service`, `AllowIsolate=yes`. Validate the final dependency graph on the chosen image. No startup through `.bashrc`, shell profiles, `rc.local`, a desktop session or root autologin.
- **Console.** Primary profile: serial console `/dev/ttyS0`, reachable through the OpenShift VM serial console and `virtctl console`. A configurable `/dev/tty1` profile serves VNC use; only the selected profile runs, with no competing getty on that terminal. The TUI unit binds the TTY (`TTYPath`, `StandardInput=tty`, `StandardOutput=tty`, `TTYReset=yes`), sets `TERM`, logs to journald, runs unprivileged, restarts independently of the worker, and returns to the application rather than a shell. Mask only the competing getty and keep a documented administrative recovery path.
- **Lifecycle.** Worker and TUI are independent; worker failure is visible from the TUI; a disconnected or restarted console never stops ingestion or publication. Set restart delays and rate limits so a broken application cannot restart-storm. Local ledger inspection and manual operations work without external network access.
- **Provisioning and persistence.** Manage VM, storage, networking and bootstrap through GitOps. The guest OS is **RHEL 10 Image Mode**. Provisioning is reproducible and idempotent with pinned application artifacts; nothing unpinned is installed from the internet on boot. The application runs natively in the guest. Ledger, audit history, file spool and settings live on a dedicated data volume; the worker requires that mount and never creates an empty ledger on the root filesystem. Rebuilding the OS disk never erases ERP state. Start with a modest allocation and record observed usage. No permanent container deployment duplicating the ERP.
- **SFTP and access.** An internal, stable SFTP endpoint reachable by the adapter, not exposed publicly by default. A dedicated SFTP-only account confined to the exchange directories, with no database access and no shell. Administrative SSH is separate and key-based. SELinux stays enforcing, with ownership, labels and rules provisioned. Persist the SSH host identity or provide a deliberate rotation procedure coordinated with the adapter's trust configuration. Direct-to-TUI startup grants ERP operations to anyone with VM-console access: restrict that through OpenShift RBAC and document the shared-console trust model.
- **Recovery and backup.** Runbooks for restarting worker or TUI, returning to the ERP target, recovering through administrative SSH or rescue boot, diagnosing missing storage and SFTP failures, application-consistent backup and restore, and rebuilding the guest while keeping the data disk. A blind copy of a live SQLite file is not a backup; use a consistent method and test the complete restore.

## Required demonstration

1. Boot the VM and open its console directly into the ERP application.
2. Leave processing in MANUAL mode.
3. Submit a fulfillment through the adapter's REST API and receive 202.
4. Observe the imported request in the TUI; hold and release it.
5. Ship it manually and observe the adapter's resulting status and event.
6. Re-emit the response; no duplicate shipment or duplicate logical completion.
7. Demonstrate a one-shot crash after shipment commit, then recover the original shipment and response.
8. Reboot the VM and verify direct-to-TUI startup with preserved state.

Also accept a request while the VM is unavailable and deliver it after the VM returns.

## Verifiable acceptance evidence

- The selected default target is `box1-erp.target`.
- A cold boot reaches the TUI without login or a launch command.
- The documented OpenShift and `virtctl` console path works.
- The TUI is functional at 80x24 and after reconnecting.
- Worker and TUI recover independently.
- Networking, SFTP and administrative recovery remain available.
- Ledger and spool survive reboot and guest replacement.
- Missing data storage fails safely without creating a new ledger.
- Adapter-to-VM file exchange works end to end.
- Backup/restore and the demonstration sequence have actual evidence.

## Nominal 64K-context implementation slices

1. Virtualization health, storage, image-build and resource decision record.
2. Image Mode guest image with pinned ERP artifact, boot target and console units.
3. VM, data volume, SFTP Service, NetworkPolicy and console RBAC as a GitOps PR.
4. Missing-disk, reboot, guest-rebuild and backup/restore exercises.
5. End-to-end demonstration with #13 and #14.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`, in place of the slices above. **Scope:** the VM, guest image, boot target, console binding, storage, networking, access controls, runbooks and appliance validation. Application changes belong to #14 and adapter changes to #13; a needed change there is a stop condition. **Run order:** start after #14's protocol specification and a pinned artifact exist; this run may proceed in parallel with #13.

**Discovery must cover (state observed 2026-11-05; verify before relying on it):**

- OpenShift `5.0.0-rc.7`. `kubevirt-hyperconverged-operator.v5.0.0` was installed through OLM in `openshift-cnv` (channel `stable`, Automatic approval) and is **not managed by `box1-gitops`**. The HyperConverged resource reported `Available=False`, `Degraded=False`; its CDI CRDs were created that day;
- DataSources in `openshift-virtualization-os-images`, including `rhel10`. Image Mode needs a bootc image build path, registry and entitlements, which the DataSource alone does not provide;
- existing VMs: `vm-sandbox/blue-whippet-32` was Running. Do not touch workloads this run did not create;
- storage: `lvms-vg1` (default, RWO, `WaitForFirstConsumer`); the node had about 31.5 CPU and 125 GiB allocatable with KVM available;
- secret management: no ExternalSecrets, Vault or SealedSecrets CRD; Vault is [#41](https://github.com/box1-org/box1-docs/issues/41). SSH keys and host keys need a provisioning answer;
- backup targets: NooBaa object storage has had availability problems ([#43](https://github.com/box1-org/box1-docs/issues/43)).

**Design decisions to record before implementation:**

- fixing HyperConverged `Available=False`: diagnosis is read-only; any change to the operator or HCO needs approval;
- whether to adopt OpenShift Virtualization into `box1-gitops`, which is an approval-required decision. Do not reinstall or reconfigure it incidentally;
- the Image Mode build: where the bootc image is built (Pipelines as Code or elsewhere), which registry holds it, how the ERP artifact is pinned, and how image updates roll out without touching the data disk;
- namespace, and whether the user names it the demo namespace for VM stop, outage and crash demonstrations, which needs approval;
- the SFTP Service type and the NetworkPolicy admitting only the adapter;
- console RBAC: who holds `virtualmachineinstances/console` and `vnc`;
- the backup target, schedule, and restore check;
- VM CPU and memory sizing against measured usage.

**Phase exit additions:**

| Phase | Must also show |
|---|---|
| 0 Discovery | Virtualization health diagnosed; nothing changed on the cluster |
| 3 Implementation | Image, units and manifests reviewed in PRs; nothing applied outside GitOps |
| 4 Verification | Boot target, console, mount and SELinux checks pass in a test VM or the documented reason they cannot |
| 6 Delivery | VM reconciled by Argo from the merged GitOps change |
| 7 Live acceptance | The required demonstration runs end to end with recorded evidence |

**Verification scenarios:** cold boot to TUI with no login; `virtctl console` and the web serial console; TUI exit and crash return to the application; worker killed while the TUI stays up; restart-rate limit holds; data volume missing at boot; reboot and guest-disk rebuild with the data disk kept; SFTP account denied shell and database; administrative SSH by key only; SELinux enforcing throughout; host key stable across rebuild; VM stopped while the adapter accepts requests, then delivered after return (needs approval as cluster fault injection); backup then restore into an isolated target with record checks.

## Final handoff

List actual repositories, paths and CRDs inspected, generated manifests and applied resources (separately), tests and observed results, GitOps PRs and commits if actually created, blocked dependencies, resource impact, rollback plan and the next bounded slice. Stop if privilege, compatibility or capacity assumptions cannot be verified. Under `frontier`, also complete the run state block of `00-shared/05_HANDOFF_TEMPLATE.md`.
