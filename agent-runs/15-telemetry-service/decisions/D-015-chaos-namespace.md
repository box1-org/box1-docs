# D-015 Namespace where chaos is allowed

**Status:** OPEN, the user names it (prompt and 06_RESOURCE_AND_SECURITY_BOUNDARIES.md).

- The image ships with chaos disabled and an empty allowlist. Two runtime settings in the workloads Deployment enable it: `ASSET_CHAOS_ENABLED=true` and `ASSET_CHAOS_NAMESPACE_ALLOWLIST=<name>`. The service reads its namespace from the downward API (`POD_NAMESPACE`), not from configuration it controls.
- The only namespace the service runs in is `asset-service-dev`. Naming it is the agent's suggestion only; nothing is enabled until the user names it and approves the workloads merge.
- Load runs without chaos are not gated by the allowlist (the prompt gates chaos), but they need the console role and are bounded by D-004.
