# D-001 Repository, namespace and run boundaries

**Status:** decided (user, 2026-11-05 23:3x EST).

- Target repository: `box1-org/notification-service`, onboarded by the user through the Golden Path (template 1.1.0) at 2026-11-06T04:29Z. The prompt's proposed name `box1-ops-notification` (PR #69 branch) is superseded by the user's instruction in this run.
- Namespace `notification-service-dev`, Argo Application `notification-service` (box1-workloads-dev `applications/notification-service.yaml`, selfHeal, no prune).
- The prompt was read from branch `notification-frontier` (0b75ee3) because PR #69 was still open at 23:33 EST.
- Writes: feature branches and PRs in `notification-service`, `box1-workloads-dev`, `box1-gitops`; contracts PRs only for the notification schemas and the `TOPICS.md` consumer-group change. Local worktrees and containers are prefixed `run16-`.
- Out of scope: the operator console (#18), order-service and every other service. A needed change there is a stop.
