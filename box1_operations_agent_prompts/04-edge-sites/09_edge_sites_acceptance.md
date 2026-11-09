# Edge sites 09 — Epic closeout: site NetworkPolicy, runbooks and end-to-end acceptance

> **The last edge-sites prompt.** It adds the least-privilege egress NetworkPolicy for each site namespace, writes the runbooks, and proves #126's acceptance criteria end to end on the cluster. It integrates and verifies; it does not re-implement what `01`–`08` own. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md`, `05_HANDOFF_TEMPLATE.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- NIC detaches, bad releases, VM rebuilds and replays are fault injections: approval needed for each, on the named site VMs only.
- The NetworkPolicy is a GitOps PR that states what merging changes. The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not touch `legacy-erp` or `vm-golden-check`. Do not use Chrome.

**Issue:** [box1-docs#126](https://github.com/box1-org/box1-docs/issues/126) (epic): the work items "egress NetworkPolicy" and "Runbooks", and every acceptance criterion.

**Dependencies:** `01`–`08` in this directory, and golden-path #136–#141 (`../03-golden-path/`, with #141 in `06_staged_site_rollout.md`). Criteria that depend on undelivered work are recorded as blocked, not claimed. The per-site Kafka identity criterion is blocked on [#71](https://github.com/box1-org/box1-docs/issues/71).

## Mission

Close the epic with evidence: every #126 acceptance criterion observed on the cluster through the real interfaces, the sites restricted to their integration points, and runbooks that let someone without this conversation disconnect, recover, roll back and rebuild a site.

## Verified baseline (observed 2026-11-09; verify before relying)

- Nothing in the epic's own scope is implemented. The golden-path code for #136–#140 merged on 2026-11-09, but those issues are open and not live-verified (run-state PRs [#145](https://github.com/box1-org/box1-docs/pull/145)–[#148](https://github.com/box1-org/box1-docs/pull/148) and [#150](https://github.com/box1-org/box1-docs/pull/150)). #141 has `../03-golden-path/06_staged_site_rollout.md`.
- **NetworkPolicies in `box1-org` are ingress-only.** No repository has an `egress:` rule. VM precedent: `box1-workloads-dev/workloads/legacy-erp/sftp.yaml` L8–47 selects `vm.kubevirt.io/name`; port 22 stays open for `virtctl ssh`.
- The sites stay outside the ambient mesh, as `legacy-erp` does (no `istio-discovery` / `istio.io/dataplane-mode` labels on the namespace).
- `box1-docs/runbooks/` has `service-decommission.md` and others; there is no site or VM-rebuild runbook. #138 updates the decommission runbook for `vm-instance`.
- Capacity: see `01`'s measurements and the [2026-11-06 PV capacity audit](https://github.com/box1-org/box1-docs/blob/main/achievements/2026/2026-11-06-pv-capacity-audit.md).

## Decided design

From #126's decisions.

**Egress NetworkPolicy (least privilege only, not the demo control)**
- One policy per site namespace (`site-west-dev`, `site-east-dev`), selecting the site's virt-launcher pod, allowing only: DNS; the Kafka bootstrap and broker pods (9092); asset-service (status API); Keycloak (token endpoint, through whatever address `03` chose); `box1-collector` (4317/4318); the internal image registry (5000, for `bootc upgrade` and quadlet images). Everything else is denied.
- Add it to the `vm-instance` bundle (coordinate with #138) or as a per-site file; record which. Prove the policy is enforced for a VM on the pod network before relying on it.
- The ingress side keeps `virtctl ssh` (port 22) for `box1-bootc-apply`.

**"Site goes dark"** is a NIC detach, never a NetworkPolicy toggle.

**Runbooks (in `box1-docs/runbooks/`)**
- Site disconnect and recovery by NIC detach, including how to read buffer depth and confirm a clean drain.
- Bad edge update: recognising a greenboot rollback, reconciling the approved digest, and retrying.
- VM rebuild and restore: re-creating a site from its instance (cloud-init identity re-applied, site data preserved or restored as `01` decided), with what is lost if the data does not survive.

## Scope and guardrails

**In scope:** the NetworkPolicy PR, the runbooks, end-to-end acceptance runs and the evidence, and repairs that are clearly inside `01`–`08`'s delivered scope (fix through that prompt's repository and record it).

**Out of scope:** new features; #134 and #135; Red Hat Edge Manager.

## Verifiable acceptance evidence

These are #126's acceptance criteria. Tick each only with the evidence named.

- [ ] Each site VM boots the digest approved for that instance, and that OS digest contains the approved `site-gateway` bundle digest. Both sites were created from Developer Hub, with no manual `oc`. The console shows `site_ds9` and `site_spacedock` online, with last-seen time and the running digest.
  - Evidence: instance annotations, `bootc status` from each guest, the `COPY --from=…@sha256:` line in the released Containerfile, the Hub task IDs, and the console.
- [ ] Readings from each site appear in asset-service, a threshold breach raises one alert and later clears it, and the trace runs from the site to the alert.
  - Evidence: from `05` and `07`, re-run here.
- [ ] **Site goes dark:** with `site-west`'s NIC detached, the site keeps recording readings and pick confirmations locally; the console shows `site_ds9` offline within a stated window; `site_spacedock` is unaffected; and order processing continues.
  - Evidence: one approved detach with timestamps, site-local counts, both sites' console states, and an order placed and shipped during the outage.
- [ ] After reattaching the NIC, the buffered backlog drains with no lost and no duplicate readings or stock movements (verified against counts recorded at the site), and the buffer stays within its stated bound during the outage.
  - Evidence: site-side counts, Kafka and service counts, and peak buffer depth against the bound.
- [ ] A site count that conflicts with central stock is resolved by the documented rule, with an audit record.
  - Evidence: from `06`, re-run here.
- [ ] **Bad edge update:** an image that fails its greenboot checks is rolled back automatically, the console shows the rolled-back digest, and the site resumes reporting.
  - Evidence: from `08`, on `site-east` only.
- [ ] Each site can write only its own status to asset-service; a write as the other site, or anonymously, is rejected.
  - Evidence: from `03` and `04`.
- [ ] Each site can write only its own `siteId` to Kafka. **Blocked on [#71](https://github.com/box1-org/box1-docs/issues/71).**
  - Evidence: from `03`'s Kafka half, once #71 lands; otherwise record `blocked`.
- [ ] agentic-operations can cite a site's last-seen gap and buffer depth when asked about a delayed site.
  - Evidence: the question, the answer and its cited evidence. If agentic-operations has no tool for site status, adding a read-only one is in scope only with approval; otherwise record it as a follow-up.
- [ ] Measured RAM, CPU and storage for both VMs are recorded, and the LVMS reservation headroom is checked before provisioning.
  - Evidence: `01` and #138's measurements, plus a fresh headroom check.
- [ ] The egress NetworkPolicy allows the integration points and denies other egress. *(Added by this prompt for #126's NetworkPolicy work item; it is not in the issue's acceptance list.)*
  - Evidence: from a guest, a successful call to each allowed endpoint and a refused connection to a non-allowed one (for example another service in the cluster).

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/126-edge-sites-acceptance/`.

**Discovery must cover**
- The handoff of every earlier prompt and the open items they left.
- NetworkPolicy enforcement for VM pods with the cluster's CNI.
- The agentic-operations tools available for site questions.

**Design decisions to record**
- NetworkPolicy placement and rules.
- The outage window and the counts recorded for the dark-site run.
- Which earlier evidence is reused and which is re-run.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 0 Discovery | A table of #126 criteria against delivered prompts, with blockers |
| 6 Delivery | NetworkPolicy reconciled by Argo; runbooks merged |
| 7 Live acceptance | Every criterion at `live_verified` or `blocked` with the reason |

**Verification scenarios**
- NIC detached on both sites at once; detach longer than the buffer bound; NetworkPolicy blocks a newly needed endpoint (the failure must be visible and documented).

**Stop conditions**
- An earlier prompt's delivery is missing for a criterion (record and continue with the rest).
- The NetworkPolicy is not enforced for VM pods.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. Include the criteria table with proof levels, runbook paths, the NetworkPolicy PR, the final digests per site, open blockers (#71, #141 if open), and the follow-ups #134 and #135. The achievement log is written separately when the user asks.

Tick the completed #126 work items and acceptance criteria.
