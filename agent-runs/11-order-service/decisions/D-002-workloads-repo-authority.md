# D-002 Authority for box1-workloads-dev

**Status:** open, user decision. Blocks Phase 6.

**Gap:** this run's standing permissions name `box1-gitops`, but service workloads live in `box1-workloads-dev`. `workloads/order-service/` is where Kafka bootstrap settings, datasource settings and the database Secret are declared. `KAFKA_BOOTSTRAP_SERVERS` is not set there, so the service would fall back to `localhost:9092`. `box1-gitops` holds shared infrastructure such as Kafka topics.

The profile allows opening a pull request in "a GitOps repository". The run's permission list is narrower, so this was not assumed.

**Requested:** permission to create feature branches, push and open pull requests in `box1-workloads-dev`. Merges stay with the user.
