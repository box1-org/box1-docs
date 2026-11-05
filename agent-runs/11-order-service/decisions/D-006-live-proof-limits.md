# D-006 Limits on live proof

**Status:** planned defaults. The user can override them. These do not block the run on their own.

**Observed:**

- No OpenTelemetry, Tempo or Loki CRDs are installed, and user workload monitoring is not enabled. Platform 02 (#22) is open.
- `box1-kafka` has no dead-letter topic. Its plain listener has no authentication or authorization.
- No demo namespace is named for fault injection.

**Defaults:**

- **Traces:** tested locally and carried in logs and events. Viewing them in a trace backend stays `blocked` on #22.
- **Metrics and logs:** live proof comes from `/q/metrics` and `oc logs`.
- **Dead-letter path:** proven locally. A `box1-gitops` PR will state what merging it creates, and the merge needs approval. `TOPICS.md` gets the additive contract change first.
- **Fault injection:** local only. No cluster fault injection in this run, so the matching #31 items remain open.
- **Requirement tags:** FR-01, FR-03, FR-04, DAT-03/04 and OBS-01/02/03 are undefined on `box1-docs` main, so the ledger uses IDs derived from prompt text.
