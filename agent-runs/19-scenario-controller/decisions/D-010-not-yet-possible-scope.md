# D-010: Scenarios with no implementation in this run

- **Status:** decided by the agent within the accepted table.
- `broker-outage`, `erp-unavailable`, `poison-event`, `bad-artifact-gate` and `red-alert` are catalog entries with `availability: NOT_YET_POSSIBLE` and a plain reason. The controller has no code that stops Kafka, stops a VM, produces to a topic or calls asset-service control. Starting them returns 409 and is audited.
- Correction to my Phase 0 wording ("local proof only"): implementing these mechanisms locally would add capabilities that are not approved for the cluster. The underlying service behavior is already proven in each service's own suite (for example inventory `brokerOutageAfterCommitLosesNothing`, consumers' dead-letter tests). This run proves the refusal.
- Available: `baseline-order`, `inventory-contention`, `erp-manual-hold`, `erp-delayed-processing`, `erp-crash-after-commit` (the last two need ERP demo faults enabled, which the run states as a prerequisite and verifies only through outcomes).
