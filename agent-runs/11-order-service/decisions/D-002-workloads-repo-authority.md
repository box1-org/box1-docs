# D-002 Authority for box1-workloads-dev

**Status:** resolved 2026-11-05 by the user: yes. Feature branches, pushes and PRs in `box1-workloads-dev` are allowed. Merges stay with the user.

**Gap:** this run's standing permissions name `box1-gitops`, but service workloads live in `box1-workloads-dev`. `workloads/order-service/` is where Kafka bootstrap settings, datasource settings and the database Secret are declared. `KAFKA_BOOTSTRAP_SERVERS` is not set there, so the service would fall back to `localhost:9092`. `box1-gitops` holds shared infrastructure such as Kafka topics.

The profile allows opening a pull request in "a GitOps repository". The run's permission list is narrower, so this was not assumed.

**Requested:** permission to create feature branches, push and open pull requests in `box1-workloads-dev`. Merges stay with the user.
