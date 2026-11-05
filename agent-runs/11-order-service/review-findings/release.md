# Release pass

Fresh subagent, read-only, 2026-11-05, against release `order-service-release-jn4rl`. Verdict: conditional. POST checks were added afterwards by the implementing session; see `../evidence/09-release.txt`.

| Item | Result | Evidence |
|---|---|---|
| Digest matches the GitOps promotion | Pass | `sha256:513c366d…b65d` in the build, PipelineRun result and `box1-workloads-dev#52` |
| Argo reports the expected revision | Pass | `order-service` Synced/Healthy at `9293ad8` |
| Running pod uses that digest | Pass | imageID matches, `gitRef` `4ec33fb` |
| Endpoints work | Pass | Reads by the reviewer. POST 201, replay 200, changed body 409, no key 400, invalid 400 by the implementing session |
| OpenAPI examples | **Fail** | Finding 3 |

## Findings

| # | Severity | Finding | Outcome |
|---|---|---|---|
| 1 | High | The gate's rejection path had never been shown through the Task. Its reports are discarded, so `policy=pass` cannot be audited. The policy lives in Central, outside Git. | Rejection shown by a TaskRun, `evidence/09-release.txt`. Auditability open in box1-docs#42. |
| 2 | Medium-high | Rollback by revert restores `fb669bff`, which has 14 `FAIL_BUILD` violations and never passed the gate. Not exercised. | Runbook change in `order-service#4`. Also in box1-docs#42. |
| 3 | Medium | Served `/q/openapi` declares POST as 200 and 400, and GET by id as 200 only. The contract declares 201, 409, 404 and examples. Smoke never calls the order API. | `order-service#4`, not merged. A broken create would still pass the new smoke. |
| 4 | Medium | The gate can be bypassed: `main` is unprotected on the service and GitOps repos, the pipeline default is `disabled`, and admission enforcement is off. | Open in box1-docs#42. Limited in practice, with one collaborator. |
| 5 | Low-medium | Gate evidence is not durable: `max-keep-runs` prunes it. | jn4rl results copied to `evidence/09-release.txt`. |
| 6 | Low | Run state was stale. | Fixed. |
| 7 | Low | Cleanup: `stackrox/roxctl-token` pod, merged `box1-gitops` branches, `box1_orders_stuck` held at 1 by a test order. | Open. |

Found after the pass by the implementing session:

| # | Severity | Finding | Outcome |
|---|---|---|---|
| 8 | Low | `Location` uses `http://` on the HTTPS Route. It works through a 302. | `order-service#4`, not merged. |
| 9 | Low | Timeline `sequence` is global, so an order's first entry may not be 1. The contract allows it, but its example implies per-order. | Open. Needs a contract decision. |

Finding 4: the direct push of `4ec33fb` was requested by the user. Tracked elsewhere: box1-docs#40, #41, #43, #44.
