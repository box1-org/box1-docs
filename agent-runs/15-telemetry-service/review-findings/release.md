# Release pass

Fresh read-only subagent, after delivery, 2026-11-06 ~02:05 UTC (21:05 EST). Anonymous GETs, oc and gh reads only. **PASS.**

Verified from primary sources: asset-service#1 merged 1706dd0b; release rmcdq Succeeded (build, security enforcement=gate
policy=pass scan-exit=0, promote, smoke "PASS: Argo Synced/Healthy, expected source and runtime digest, REST, Java 21,
health, OpenAPI, metrics, validation"); promotion box1-workloads-dev#72 (7a90162e) changes only workloads/asset-service
digest and annotations; Argo asset-service Synced/Healthy at 7a90162e; Deployment and pod imageID
sha256:6d8e8c172b2885f35a551eb34c53429e1ac85a1771263ba841795c683fbde944; /api/info gitRef 1706dd0b; readiness UP
(database, messaging, projection); console 302 with https redirect_uri and PKCE; /signed-out.html headers; inventory and
order Deployments unchanged; the contract's three operations exist in the served OpenAPI.

| Finding | Outcome |
|---|---|
| REL-1 (low) Anonymous 401s have an empty body with `WWW-Authenticate: Bearer`, not problem+json; consistent with the contract and served spec | Recorded: problem+json applies to 400/413/429/503. Docs claim nothing else. |
| REL-2 (low) Served OpenAPI for the two reads lacks the role scopes and 400/401 responses the shared contract lists | Follow-up: add `@SecurityRequirement` scopes and `@APIResponse` 400/401; needs a release, so not done in this run |
| REL-3 (info) Rollback: reverting 7a90162e restores sha256:0dc4185e (image still present); not exercised | Recorded as not tested |
| Info: `box1-kafka` is OutOfSync on `box1.fulfillment.dlq.v1` (another run's topic) | Existing condition, not this run's; not touched |

Not verified: authenticated reads, ingestion POST, console login, rollback execution, RHACS violation detail beyond policy=pass.
