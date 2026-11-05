# D-013 External, internal and administrative endpoints

**Status:** decided by the agent in Phase 1, 2026-11-05.

- **External, unauthenticated by decision D-003:** `/api/v1/orders*`.
- **Platform, unauthenticated because the smoke task requires it:** `/api/greetings`, `/api/info`, `/q/health/*`, `/q/openapi`, `/q/metrics`, `/q/swagger-ui`.
- **Internal or administrative:** none exist. A test asserts representative internal paths return 404. This is weaker than proving access control, so `ORD-VS-AUTHZ` records that limitation.
- The scaffold's greeting endpoint and metric stay.
