# D-001 ERP implementation repository

**Status:** resolved 2026-11-05 about 18:50 EST: the user created `box1-org/box1-ops-erp-simulator` (public, empty). The run pushed one empty commit to `main` (`db73db3`) so the code could arrive by PR, then the full history on `erp-appliance` as [PR #1](https://github.com/box1-org/box1-ops-erp-simulator/pull/1).

**Finding:** no ERP repository exists in `box1-org` (evidence/00-discovery.txt). The prompt proposes `box1-org/box1-ops-erp-simulator`. The order pilot used `order-service` rather than `box1-ops-order`, so the name is the user's choice.

**Recommendation:** create `box1-org/box1-ops-erp-simulator`, **public**, created with `gh repo create` (not Developer Hub: the only templates are the Quarkus Golden Path and a no-build `github-repository`, and the onboarding plugin rejects non-Deployment workloads per #46). Public matches every other service and contracts repository; the code holds no credentials. Add `catalog-info.yaml` so it can be registered in Developer Hub later.

**Alternatives:** `erp-simulator` (matches the `order-service`/`inventory-service` naming actually used); private (only `rhel-image-poc` is private; no reason here).

**Until approved:** development continues in a local repository at `/Users/mike/Documents/ChatGPT/box1/run14-erp` with no remote. Nothing is pushed.
