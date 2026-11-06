# Pipelines console: View SBOM and Vulnerabilities for release runs

**Date:** 2026-11-05 (America/New_York), about 21:00–23:10 EST
**Status:** Delivered for the four gated services and `quarkus-reference`. Three service PRs are still open. The rendered console page was not checked. Tracked in [box1-docs#57](https://github.com/box1-org/box1-docs/issues/57). A Pipelines as Code start failure hit along the way; it is tracked in [#64](https://github.com/box1-org/box1-docs/issues/64) and [#42](https://github.com/box1-org/box1-docs/issues/42).

## Outcome

Release runs that use `box1-security-gates` now give the OpenShift Pipelines console what it needs for two features:

- **View SBOM** links to the run's SBOM in RHTPA.
- The **Vulnerabilities** column gets RHACS critical, high, medium and low counts for the released image digest.

Before this, every release run showed "View SBOM is not applicable for this PipelineRun" and `-` in the column. That was true even when the gate had uploaded an SBOM and scanned the image. The data existed only as task results under names the console does not read.

Five services were released after the change. Every release succeeded, and every one emitted both values:

| Service | Release | Mode | `SCAN_OUTPUT` (C/H/M/L) | Promotion |
|---|---|---|---|---|
| `quarkus-reference` | `quarkus-release-5n54k` | observe | 1 / 17 / 187 / 94 | [workloads-dev#81](https://github.com/box1-org/box1-workloads-dev/pull/81) |
| `fulfillment-adapter` | `fulfillment-adapter-release-ckkb4` | gate | 0 / 10 / 153 / 83 | [#84](https://github.com/box1-org/box1-workloads-dev/pull/84) |
| `inventory-service` | `inventory-service-release-66zjv` | gate | 0 / 10 / 153 / 83 | [#86](https://github.com/box1-org/box1-workloads-dev/pull/86) |
| `order-service` | `order-service-release-j2r9q` | gate | 0 / 10 / 153 / 83 | [#87](https://github.com/box1-org/box1-workloads-dev/pull/87) |
| `asset-service` | `asset-service-release-vg2nn` | gate | 0 / 10 / 153 / 83 | [#88](https://github.com/box1-org/box1-workloads-dev/pull/88) |

The four gated services report identical counts, which fits a shared base image; that was not checked further. `quarkus-reference` reports more, and RHACS policy would reject its image. That run was `observe`, so it was report-only and promotion went ahead.

## Starting baseline

- `asset-service-release-qr6nl` ran with `security-gates=gate`. Its security TaskRun produced `rhtpa-sbom-url`, `sbom-id`, `findings=scan-exit=0` and `policy=pass`, yet the console showed no SBOM link and no counts.
- `quarkus-reference` released with `security-gates: disabled`. It produced no SBOM and no scan.
- `box1-security-gates` had no console annotations and no `LINK_TO_SBOM` or `SCAN_OUTPUT` result. No release pipeline exposed a scan result at pipeline level.

## The console contract

The rules below were read from upstream [`openshift-pipelines/console-plugin`](https://github.com/openshift-pipelines/console-plugin) (`pipeline-utils.ts`, `usePipelineRunVulnerabilities.ts`). The deployed `pipelines-console-plugin` bundle (Pipelines 1.24.3) uses the same rules.

- **View SBOM** looks for a **TaskRun** annotated `task.results.key: LINK_TO_SBOM` and reads that TaskRun's `LINK_TO_SBOM` result. With `task.results.type: external-link` it opens the value as a URL; without it, the console shows the task log.
- **Vulnerabilities** sums **PipelineRun** results whose name ends in `SCAN_OUTPUT`, in the form `{"vulnerabilities":{"critical":N,"high":N,"medium":N,"low":N}}`. Any matching result renders as counts, **even an empty or unparseable one**. So the result must be omitted when no scan ran, or the column would show false zeros.
- Task annotations reach the TaskRun through the cluster resolver. The live TaskRun already carried the Task's `box1.org/security-gate` label, and the new annotations arrived the same way.
- Tekton does not fail a TaskRun that leaves a declared result unwritten. A pipeline result that references the missing result is simply not emitted.

## What changed

| Area | PR | Merge | Change |
|---|---|---|---|
| Task | [box1-gitops#70](https://github.com/box1-org/box1-gitops/pull/70) | `9f2293e` | `box1-security-gates`: the two annotations, `LINK_TO_SBOM` (the RHTPA SBOM page, written only after a successful upload), and `SCAN_OUTPUT` built from roxctl `result.summary` (CRITICAL→critical, IMPORTANT→high, MODERATE→medium, LOW→low; written only when the scan exits 0 with a summary) |
| Template | [box1-templates#28](https://github.com/box1-org/box1-templates/pull/28) | `badc3c3` | Quarkus skeleton release pipeline exposes `SCAN_OUTPUT` |
| Test service | [quarkus-reference#4](https://github.com/box1-org/quarkus-reference/pull/4) | `c8367db` | `security-gates: disabled` → `observe`, and adds `SCAN_OUTPUT`, with a defect (see below) |
| Test service | [quarkus-reference#5](https://github.com/box1-org/quarkus-reference/pull/5) | `69098db` | Fix: `SCAN_OUTPUT` moved into the existing `results` block |
| Test service | [quarkus-reference#6](https://github.com/box1-org/quarkus-reference/pull/6) | `3e27018` | Empty commit to re-run the release after the PaC failure |
| Services | [fulfillment-adapter#3](https://github.com/box1-org/fulfillment-adapter/pull/3), [inventory-service#2](https://github.com/box1-org/inventory-service/pull/2), [order-service#5](https://github.com/box1-org/order-service/pull/5), [asset-service#3](https://github.com/box1-org/asset-service/pull/3) | `4c98522`, `094772a`, `11360f2`, `0d717d0` | `SCAN_OUTPUT` pipeline result |

**Made outside Git:**

- Argo CD sync of `pipelines-ci` at `9f2293e`, limited to the `box1-security-gates` Task. `pipelines-ci` has no automated sync.
- Cancelled the orphaned PipelineRun `box1-gitops-validate-82khc`, and closed the stranded promotion PR [workloads-dev#79](https://github.com/box1-org/box1-workloads-dev/pull/79).

**Decisions:**

- **Merge order is a hard dependency.** A release pipeline that references `$(tasks.security.results.SCAN_OUTPUT)` while the live Task does not declare it fails with `InvalidTaskResultReference`. The Task went first and was synced before any pipeline change merged.
- **`quarkus-reference` now runs the gate in `observe`.** The test needed a real SBOM and scan; `observe` reports without blocking promotion.
- **The SBOM link points at RHTPA**, where Box1 already stores SBOMs, rather than at an SBOM attached to the image.

## Correction during the work

`quarkus-reference#4` added a second `pipelineSpec.results` key. Each release file already declared `results:` further down. YAML keeps the last duplicate key, so `SCAN_OUTPUT` was silently dropped: run `quarkus-release-hqc5k` emitted only `image-digest`, `gitops-pr` and `gitops-revision`. The server-side dry run could not catch this, because parsing had already merged the keys.

It was fixed in `quarkus-reference#5` and in `box1-templates#28` before that PR merged. Every later edit was checked with a duplicate-key scan, a parse that lists the pipeline results, and `oc create --dry-run=server`. The scan does flag the broken `c8367db` file.

## Validation and evidence

- **Task logic:** I ran the `SCAN_OUTPUT` block locally against a roxctl-shaped summary, and it wrote the expected counts. With a non-zero exit, non-JSON output or a missing summary, it wrote nothing.
- **Live Task after the sync:** carries both annotations, and its results include `LINK_TO_SBOM` and `SCAN_OUTPUT`.
- **`quarkus-release-5n54k`** (commit `3e27018`) passed build, security, promote and smoke. The deployment now runs `box1-ci/quarkus-reference@sha256:ccf7ffa3d1f8f57dc549b9dbd88c20660c40b4bfa4b02846c0ee5a052f6f8fa5`.
  - The security TaskRun has `task.results.key=LINK_TO_SBOM` and `task.results.type=external-link`.
  - `LINK_TO_SBOM=https://tpa.apps.ocp.box1.org/sboms/urn:uuid:01a1aee4-86e9-706f-8961-210b13dc564c`.
  - The PipelineRun's `SCAN_OUTPUT` matches the `RHACS vulnerability counts` line in the task log.
- **The four gated services** each released through build, security, promote and smoke (`order-service` also passed `order-api-smoke`). Each produced both values; see the Outcome table.

**Not verified:**

- **The rendered console.** I did not open the PipelineRun list or details page to see View SBOM enabled and the counts displayed; only the underlying TaskRun and PipelineRun data was checked. The RHTPA link was not opened either.
- **A `disabled` run** showing "not applicable" and `-`. Only the local test covers this case.

## Pipelines as Code start failure

The first release after the fix, `quarkus-release-q9wqv`, failed at promote.

- **03:10:39 UTC:** PaC created `box1-gitops-validate-82khc` for promotion PR [workloads-dev#79](https://github.com/box1-org/box1-workloads-dev/pull/79). Its `PATCH …/check-runs/127686653631` returned `404 Not Found`.
- PaC never marked the run `queued`, the watcher never enqueued it, and it stayed `PipelineRunPending`.
- GitHub reported the check as "pipelinerun start failure", and `box1-gitops-promote` failed on it as a required check. A legacy-erp promotion was validating at the same moment; its role is not established.
- **`/retest` did not recover it.** Commit comments `/retest quarkus-release-` and `/retest quarkus-release- branch:main` both failed in PaC with an empty `default_branch` and a 404.
- **Recovery:** cancel the orphan, close #79, and push a new commit (`quarkus-reference#6`). That release succeeded.

**This failure mode was already on record** in a #42 comment from the order-service delivery ([log](2026-11-05-order-service-delivery.md)). #64 was filed without catching that, so it duplicates the finding with one new occurrence. Both issues now cross-reference each other. Whether to keep #64 as the dedicated tracker or close it is the owner's call.

## Final operational state

- `box1-security-gates` in `box1-ci` is Argo CD managed (`pipelines-ci`) at `box1-gitops` `9f2293e`. The live Task matches source `main`.
- New Quarkus services from the template expose `SCAN_OUTPUT`. Their `security-gates` default is still `disabled` ([#42](https://github.com/box1-org/box1-docs/issues/42)), so they show no SBOM or counts until a service opts in.
- `quarkus-reference`, `fulfillment-adapter`, `inventory-service`, `order-service` and `asset-service` all expose the result on `main`. `quarkus-reference` is Argo CD `Synced`/`Healthy` on the digest above.
- **Still open:**
  - [legacy-erp#1](https://github.com/box1-org/legacy-erp/pull/1)
  - [vm-golden-check#2](https://github.com/box1-org/vm-golden-check/pull/2)
  - [box1-ops-erp-simulator#3](https://github.com/box1-org/box1-ops-erp-simulator/pull/3): its release pipeline is marked "NOT YET RUN on the cluster" in its own header.

## Recovery and follow-ups

**Rollback:**

- **Pipeline results:** revert the service or template commit to remove `SCAN_OUTPUT`. This is untested but low-risk, because the Task keeps working without it.
- **Task change:** revert `9f2293e` and sync `pipelines-ci`. Revert every pipeline that references `SCAN_OUTPUT` **first**, or those releases fail with `InvalidTaskResultReference`.
- **`quarkus-reference` gate mode:** set `security-gates` back to `disabled` in `.tekton/release.yaml`.

**Follow-ups:**

- [#57](https://github.com/box1-org/box1-docs/issues/57): check the rendered console, test a `disabled` run, merge the three open service PRs.
- [#64](https://github.com/box1-org/box1-docs/issues/64) / [#42](https://github.com/box1-org/box1-docs/issues/42): the Pipelines as Code check-run 404, a promote retry for a check that failed to start, and a supported way to re-run a release for an existing commit.
- [#42](https://github.com/box1-org/box1-docs/issues/42): the default security mode. With it at `disabled`, new services get none of this.
