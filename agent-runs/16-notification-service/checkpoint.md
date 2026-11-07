# Checkpoint: box1-docs#16 notification service (frontier)

## Current phase

Phase 7 complete for everything that can be proven on this cluster (2026-11-06 13:45 EST). Handoff is complete.

## Final state

| Item | Value |
|---|---|
| Image | `sha256:69788422d2f3beef94a255e4247ba3142f662f9edb25018489f2058edd5b363a`, from notification-service `bacc353` |
| Argo | Synced/Healthy at box1-workloads-dev `ef17294`; Argo CD manages it |
| Env | Floor `2026-11-06T18:03:00Z`; console tokens accepted for reading; stub faults enabled in `notification-service-dev` only |
| DLQ | `box1.notification.dlq.v1`: 3 partitions, 7 days. Listed in `TOPICS.md` |
| Ledger | 8 `live_verified`, 13 `deployed` |

## Remaining (not proven on the cluster; locally or CI proven)

- Duplicate event and same-fact-from-two-events: deployed, not exercised live.
- Retryable shipment-failure notice and an actual shipment notice: need ERP-path traffic, which is not established on this cluster.
- Exhaustion to FAILED, permanent 4xx, TTL expiry, refusal outside the allowlist, poison and replay, broker outage, shutdown with a retry pending: local only.
- 403 for a token lacking only the reader role: CI only. The issued user holds the role.

## Follow-ups (not blocking)

- Expose `actor_subject` in `GET /api/v1/stub/faults/audit`. It is stored but not returned.
- A pre-merge prerequisite check in the promote task, so a service released before its runtime settings can't deploy a crashing pod (platform change; release review H1, `evidence/06`).
- Alerts (ServiceMonitor/PrometheusRule) when #22 lands.
- A separate migration owner for the audit trigger (#41).

## Branches, worktrees

All PRs are merged. Worktrees `run16-*` can be removed after the user's achievement log. No containers are running.

## Exact next action

None for this run, unless the user asks for the achievement log or the follow-ups.
