# User decisions applied (2026-11-06 ~13:30–13:45 EST)

The user answered Q-1, Q-4, Q-5 and Q-6. Each change was merged, and synced where needed, under that approval.

| Decision | Change | Result |
|---|---|---|
| Q-1: accept console tokens for reading | box1-workloads-dev#113 (`ef17294`): `NOTIFY_AUTH_CONSOLE_CLIENT_ID=operations-console`, `NOTIFY_JWT_AUDIENCES=notification-service,operations-console` | Argo Synced/Healthy at `ef17294`; env on the Deployment; same digest `sha256:69788422…`; readiness 200 |
| Q-4: demo namespace `notification-service-dev` | Same PR: `NOTIFY_STUB_FAULTS_ENABLED=true`, `NOTIFY_STUB_FAULT_NAMESPACES=notification-service-dev` | Gate config deployed. Not exercised: needs a token with `notification-fault-operator` |
| Q-5: `TOPICS.md` DLQ row | box1-ops-contracts#11 (`c2b10e4`). `npm test` 77/77 and validate PASS | Merged |
| Q-6: DLQ retention 7 days | box1-gitops#80 (`73d482e`), then a selective `box1-kafka` sync of `KafkaTopic box1.notification.dlq.v1` (revision `73d482e`, prune false) | Sync Succeeded. `retention.ms=604800000`, Ready, generation 2/2 observed |

#113 checks: `box1-gitops-validate` and `box1-phase1-smoke` passed. #80 checks: `box1-onboarding-plugin-guard` and `box1-phase1-smoke` passed. #11: no CI configured; checked locally.
