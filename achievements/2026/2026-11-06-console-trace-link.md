# Operations console: order trace evidence links to the OpenShift trace viewer

**Date:** 2026-11-06 (America/New_York), about 17:20–17:35 EST
**Status:** Delivered to development. Unit tests pass, and the new revision is deployed and confirmed running. The link has **not been opened in a browser**, and the Playwright e2e suite was **not run**. Part of [box1-docs#22](https://github.com/box1-org/box1-docs/issues/22).

## Outcome

On order detail and incident evidence, the **Trace** item is now a link to that order's trace. It opens in the OpenShift console's Observe > Traces view for the `box1` Tempo instance in `box1-observability`, tenant `dev`:

```
https://console-openshift-console.apps.ocp.box1.org/observe/traces/{traceId}?namespace=box1-observability&name=box1&tenant=dev
```

`{traceId}` is the order's W3C trace ID. Before this change, the item was a placeholder: "No trace, log or dashboard backend is deployed yet (box1-docs#22)". Distributed tracing now exists (for example, trace `aa4f7efc117e3b1e8b160568b4e26725` for `POST /api/v1/orders`), so an operator can go from an order straight to its trace.

This completes the "unfinished trace-link change" that the console asset-alerts log ([box1-docs#84](https://github.com/box1-org/box1-docs/pull/84), unmerged at the time of writing) records as uncommitted.

## Starting baseline

- `operations-console` `main` at `43f4d28`. The deployed digest was `sha256:45874d64…`, from promotion [workloads-dev#131](https://github.com/box1-org/box1-workloads-dev/pull/131).
- The console already exported traces. The dev overlay sets `QUARKUS_OTEL_TRACES_SAMPLER_ARG=1.0` and the `box1-collector` OTLP endpoint ([workloads-dev#136](https://github.com/box1-org/box1-workloads-dev/pull/136)).
- The Trace evidence item was hard-coded as unavailable. The Logs and Dashboard items were too.
- An uncommitted draft of this change existed on branch `trace-link` from an earlier session. Its tests had not been run.

## What changed

[operations-console#10](https://github.com/box1-org/operations-console/pull/10), merge commit `e5dc0ec4432ad3e6fe87ceca5865e750a22c784e`:

- **New setting** `console.trace-url-template`, overridable with the env var `CONSOLE_TRACE_URL_TEMPLATE`. The default is the URL above.
  - It omits the `start=30m` and `q=` search parameters of the console URL, so the link does not depend on a search time window.
- **When there is no link:** the item shows the trace ID without a link, with a reason, in two cases:
  - the template is empty or has no `{traceId}`;
  - the order's trace ID is missing, not 32 lowercase hex characters, or all zeros.
- **Unchanged:** Logs and Dashboard evidence still say "not available", because no log store exists ([#82](https://github.com/box1-org/box1-docs/issues/82)).
- **Defect found and fixed during testing:** the default was first written as `${CONSOLE_TRACE_URL_TEMPLATE:https://…/{traceId}?…}`. SmallRye Config ends the expression at the `}` of `{traceId}`, which corrupted the template, so the link silently disappeared.
  - The default is now set directly. Quarkus still maps `CONSOLE_TRACE_URL_TEMPLATE` onto the property.
  - A comment in `application.properties` records why.
- **Tests and docs updated:**
  - `UpstreamBehaviourTest` asserts the exact link.
  - `flow.spec.ts` (e2e) expects the link.
  - `docs/architecture.md` describes the setting.

No change to `box1-workloads-dev` was needed: the overlay does not set the template.

## Validation and evidence

| Check | Result |
|---|---|
| `./mvnw verify` on the final change | 64 tests, 0 failures. The first run failed on the trace-link assertion, which exposed the `${…}` defect above. |
| Release pipeline `operations-console-release-mh6cn` (22:28:33–22:32:31 UTC) | build, security, promote, smoke and console-smoke all `Succeeded`. Digest `sha256:c52deca4f0f52a3595396c0e20c97e500d52abb65c912c989d37b8a8b23b6199`. `SCAN_OUTPUT` 0 critical / 10 high / 158 medium / 83 low. |
| Promotion [workloads-dev#139](https://github.com/box1-org/box1-workloads-dev/pull/139) | Created and auto-merged by `app/box1-pipelines` after `box1-gitops-validate` and `box1-phase1-smoke` passed (merge `3b74650`) |
| Argo CD `operations-console` | `Synced`, `Healthy`. The single pod runs the digest above. |
| `GET https://operations-console-dev.apps.ocp.box1.org/api/info` | `gitRef: e5dc0ec4432ad3e6fe87ceca5865e750a22c784e` |
| Anonymous `GET /api/v1/orders/{id}/summary` | 401, as expected |

**Not tested:**

- **The live link:** the signed-in order page was not opened, so the link in production has not been seen. The trace viewer was not opened either; that attempt was blocked by the agent's permission policy.
- **The trace viewer without `start`:** whether it resolves a trace by ID without a `start` parameter is **not verified**.
- **Playwright e2e:** the suite was not run. The workstation has no Playwright chromium and has Node 25, while the suite pins Node 24.

## Final operational state

- `operations-console-dev` runs `e5dc0ec` (digest `sha256:c52deca4…`), managed by Argo CD from `box1-workloads-dev` `main`. There is no manual override.
- The trace link uses the image's built-in default template. Opening a trace requires OpenShift console access to `box1-observability`.

## Recovery and follow-ups

- **Remove the link without a rollback:** set `CONSOLE_TRACE_URL_TEMPLATE=` (empty) in the `operations-console-config` ConfigMap generator of `box1-workloads-dev`.
- **Full rollback:** revert [workloads-dev#139](https://github.com/box1-org/box1-workloads-dev/pull/139), which restores digest `sha256:45874d64…`.
- Neither path was exercised.
- **Follow-up:** with an OpenShift-authorized user, open a recent order in the console and follow its Trace link. Confirm the trace renders, and add `start` to the template if the viewer needs it.
- **Follow-up:** run the e2e suite on Node 24 with Playwright browsers installed.
