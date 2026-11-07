# D-011 Suggested actions (proposal only)

**Status:** decided by the user (approval workflow deferred); the allowlist is proposed.

- **Allowlisted types:** `INSPECT_ERP_CONSOLE`, `CHECK_BROKER`, `CHECK_INVENTORY_STOCK`, `REVIEW_DEPLOYMENT`, `ROLLBACK_DEPLOYMENT_PROPOSAL`, `ESCALATE_TO_OPERATOR`, `NO_ACTION`.
- Each action carries `executable: false`, `expectedEffect` and `rollback` text. There is no endpoint, MCP tool or connector that executes anything. Tests confirm that the REST and MCP surfaces contain no write route or tool.
- `PROPOSED → APPROVED → EXECUTED/REJECTED` is deferred to a follow-up issue together with persistent state.
