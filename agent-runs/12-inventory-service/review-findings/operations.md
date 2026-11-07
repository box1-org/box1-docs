# Operations pass

Reviewed `9d6deed` by reading code and docs. The reviewer's cluster access failed on one attempt, so task versions came from `box1-gitops`. No high findings.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| M1 | Medium | First-deploy merge order undocumented. | **Fixed.** Runbook section added. |
| M2 | Medium | Consumer lag had no documented measure, and event age is silent when stalled. | **Fixed.** Command documented. Client lag meter names to confirm live. |
| M3 | Medium | Replay could not be carried out as written. | **Fixed.** Exact commands. Local saga exercises the produce command. |
| L1 | Low | Unknown dead-letter depth read as 0, and the failure counter was shared. | **Fixed.** `-1`, tagged by source. |
| L2 | Low | Broker-outage signal could stay silent. | **Fixed** in runbook. |
| L3 | Low | `inventory-api-smoke` unguarded when promotion is skipped. | **Fixed.** Same `when` as smoke. |
| L4 | Low | Floor doc scope, and skipped events distorted event age. | **Fixed.** |
| L5 | Low | Log and trace gaps. | **Fixed.** Coordinates on dead-letter lines, logging inside the scope, publisher MDC, span attribute. |
| L6 | Low | Doc gaps, no exit on heap OOM, no scrape. | **Fixed**, with `JDK_JAVA_OPTIONS=-XX:+ExitOnOutOfMemoryError` on the Deployment. Scraping stays absent (box1-docs#22). |

Not established by the reviewer: memory fit in 512Mi, and readiness after the database returns. Both are covered by the local saga: see `evidence/`.
