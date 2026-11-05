# Operations pass

Reviewed commit 764ada1 in a fresh subagent, by reading only. These same-model passes do not replace human PR review or CI. Fixes landed in 078f341, retested with the full container suite.

| Severity | Finding | Outcome |
|---|---|---|
| Medium | Runbook named the wrong broker pod | **Fixed** and checked against the cluster. |
| Medium | Connector's 60 s unprocessed-record limit could fail liveness during a database outage with a backlog | **Fixed by config.** Set to `-1`. Not exercised with a backlog. The crash loop on restart during an outage is documented. |
| Medium | JVM fit not established at 70% of a 512Mi limit | **Fixed in the workload PR.** 50%. Not yet measured on the cluster. |
| Medium | Runbook had no replay command | **Fixed.** Commands tried against a local broker only. |
| Low | Memory request below measured use | **Fixed in the workload PR.** 256Mi. |
| Low | Publish-failure logs lacked `orderId` | **Fixed.** |
| Low | Frozen gauges and refresh-failure counter undocumented; deploy order | **Fixed** in the runbook and PR prerequisites. |

Not exercised: smoke task against this image, Flyway with the deployed login, `/tmp` limit under load. These wait for Phase 6.
