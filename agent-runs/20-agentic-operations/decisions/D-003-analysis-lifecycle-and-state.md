# D-003 Analysis lifecycle and in-memory state

**Status:** the store was decided by the user (in-memory, bounded), and the user reconfirmed it on 2026-11-06 22:45 EST after weighing PostgreSQL. The values below are proposed.

- The operation ID is `ana_` plus a random UUID without dashes. The ID is not guessable and carries no data.
- Statuses: `QUEUED`, `RUNNING`, `COMPLETED`, `DEGRADED` (some evidence unavailable, analysis produced), `MODEL_UNAVAILABLE`, `MODEL_INVALID_OUTPUT`, `BUSY` (rejected at submit), `FAILED`.
  - `GET` on an unknown or evicted ID returns `404 ANALYSIS_NOT_FOUND`, with the body noting that analyses do not survive a restart.
- Store: a Caffeine cache with at most `AIOPS_ANALYSIS_MAX=200` entries and a TTL of `AIOPS_ANALYSIS_TTL=24h` after completion.
  - Each entry stores its caller's subject. `GET` is allowed for the creator and for any `aiops-viewer` (operator-only roles, D-005).
- The Deployment has `replicas: 1`, documented. With more than one replica, `GET` would miss analyses held on another pod, so scaling up is a follow-up that needs a shared store.
- No analysis is regenerated on read. A result is produced once, then served unchanged.

## Why not PostgreSQL in v1 (user decision, 2026-11-06)

- **Nothing in v1 needs durability:**
  - analyses are derived data; the facts stay in the owning services;
  - the Kafka window rebuilds on startup;
  - a lost analysis costs one more model call.
- **A per-service Postgres pod is cheap in capacity:** the existing Golden Path ones use about 30–45 Mi of memory and about 5m CPU each (`oc adm top`, 2026-11-06). It is costly in operations:
  - a database credential, pending #41;
  - a persistent volume;
  - migrations and backups;
  - a 14th Postgres pod on the single node.
- **Revisit with the approval workflow:** approval and execution records must be durable and auditable. The deferred runbook index would likely need pgvector. Tracked in [#97](https://github.com/box1-org/box1-docs/issues/97).

## Amendments (review A-2, A-7, 2026-11-06)

- The TTL counts from completion. An unfinished entry is held for the TTL from creation.
- A submission reserves its queue slot before writing the store, so a BUSY rejection never evicts an existing analysis.
- If every finding the model makes is uncited, the summary is replaced with fixed text (A-1).
