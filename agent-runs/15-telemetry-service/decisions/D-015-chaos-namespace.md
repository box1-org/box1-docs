# D-015 Namespace where chaos is allowed

**Status:** OPEN, the user names it (prompt and 06_RESOURCE_AND_SECURITY_BOUNDARIES.md).

- The image ships with chaos disabled and an empty allowlist. Two runtime settings in the workloads Deployment enable it: `ASSET_CHAOS_ENABLED=true` and `ASSET_CHAOS_NAMESPACE_ALLOWLIST=<name>`. The service reads its namespace from the downward API (`POD_NAMESPACE`), not from configuration it controls.
- The only namespace the service runs in is `asset-service-dev`. Naming it is the agent's suggestion only; nothing is enabled until the user names it and approves the workloads merge.
- Load runs without chaos are not gated by the allowlist (the prompt gates chaos), but they need the console role and are bounded by D-004.

## Update 2026-11-05 ~20:10 EST

The user deferred naming the namespace ("another day"). Chaos stays off: `ASSET_CHAOS_ENABLED=false` and an empty allowlist in the workloads Deployment. The console disables the chaos option and explains why; the service refuses chaos runs regardless. The Phase 7 "random chaos run on the cluster" is therefore blocked by this decision; the seeded load run is not.
