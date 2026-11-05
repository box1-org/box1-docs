# D-001 Implementation target repository

**Status:** open, user decision. Blocks Phase 3 pushes and everything after it.

**Conflict:** the prompt proposes `box1-org/box1-ops-order`, which does not exist. `box1-org/order-service` does exist. Developer Hub created it at 2026-11-05 02:08 EST, with description "Transactional state of customer requested orders", owner `user:default/mike4263`, PostgreSQL and Kafka both selected, and a deployed `order-service-dev` namespace. It holds only scaffold code. No prompt or doc mentions it, and the evidence does not show why it was created.

The prompt also protects a validated `orders-service` demo. That repository, namespace and Argo Application no longer exist, so its guard (`ORD-GUARD-DEMO`) has nothing to protect.

**Options:**

- **A (recommended): build in `order-service`.** No onboarding, and it already has the Route, database and pipeline. The prompt text would need correcting to the real name.
- **B: onboard `box1-ops-order`.** Matches the prompt and the other proposed `box1-ops-*` names, but needs separate approval, and leaves two order services until `order-service` is decommissioned under `runbooks/service-decommission.md`.

**Evidence:** `evidence/00-repositories.txt`, `evidence/01-cluster-baseline.txt`.
