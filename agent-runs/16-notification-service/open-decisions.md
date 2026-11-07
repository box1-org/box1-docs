# Open decisions for the user (#16)

Updated 2026-11-06 13:25 EST, after deployment.

## Resolved

| # | Decision | Outcome |
|---|---|---|
| O-1 | DLQ topic and its sync | Topic merged (#75) and synced selectively; Ready. The `TOPICS.md` row is still open, as Q-5 below. |
| O-3 | Database Secret | Created by the user |
| O-6 | Merges | All merged. Delivery went out of order and recovered (`evidence/06`). |
| O-8 | Event floor | `2026-11-06T18:03:00Z` (#110) |

| Q-1 | Console tokens | Accepted for reading (#113) |
| Q-4 | Demo namespace | `notification-service-dev`; gate enabled (#113). Each run still needs approval |
| Q-6 | DLQ retention | 7 days (#80, synced) |

| Q-2 | Keycloak roles | Confirmed by the user; both roles appear in issued tokens |
| Q-3 | Live checks | User issued login `claude`; live acceptance done (`evidence/09`) |

## Still open

None. Follow-ups that are not decisions are listed in checkpoint.md.
