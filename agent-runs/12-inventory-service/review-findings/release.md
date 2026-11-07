# Release pass

Reviewed the deployed release read-only: `oc get`, `oc logs`, `gh`, HTTP GET and offset describes. A fresh agent. **Verdict: conditional.**

Passed: build digest = promotion digest (`box1-workloads-dev#58`) = Argo revision `cd0c280` Synced/Healthy = pod imageID `sha256:d21ab42b…`. `/api/info` gitRef is `6b722a3` = source main. Live env equals workloads main. Gate ran with `enforcement=gate`, `policy=pass`, SBOM ID recorded. Served OpenAPI matches the contract's operations and response codes. Live GET shapes match. Flyway applied V1 and V2. Group `inventory` lag 0. No difference from source main.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| M1 | Medium | `inventory-api-smoke` step log looked empty | **Resolved.** `oc logs --all-containers` on the pod shows `PASS: mutations need a token, read routes have no mutation, read policy status 200, OpenAPI served. Nothing was written.` The reviewer read only one container. |
| M2 | Medium | No post-floor event has been consumed live, so the reservation, outbox and Order round trip are unproven on the cluster | **Open.** Needs the live acceptance order, which needs the user's approval. |
| L1 | Low | Served OpenAPI is looser than the contract: string `limit` and `offset`, no patterns, different schema names | Follow-up. Runtime validation enforces the bounds. |
| L2 | Low | Contract examples use `$ref` inside `example`, which OAS 3.1 treats as literal. One Problem example is reused for every 4xx. | Follow-up for `box1-ops-contracts`. The local validator dereferences them, which hid this. |
| I1 | Info | Promotion PR merged by the pipeline with no human review | Platform design (#42) |
| I2 | Info | Runtime env came from earlier workloads commits, not #58 | Expected by design |
| I3 | Info | Postgres pod 2 restarts, `ContainerStatusUnknown` | Node event; not investigated |

Rollback, reasoned and not exercised: reverting #58 restores the scaffold digest `4a1ae810…`, still in the registry. It has no datasource, so it should start against the migrated database. Tables and group offsets remain. A roll forward should find V2 applied.
