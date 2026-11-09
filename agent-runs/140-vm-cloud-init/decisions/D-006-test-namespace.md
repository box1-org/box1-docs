# D-006 Test environment

- Proposed: build a throwaway `cloudinit-check` repository through Developer Hub with `cloudInit: true` (approval: onboarding), then a namespace `cloudinit-test` with instances `ci-west` and `ci-east` from that disk digest (approval: namespace, a RoleBinding in `box1-ci`, Secrets, VMs). Manifests and steps: `test-plan/`.
- A random placeholder string stands in for the Keycloak client secret until #131 provides clients. It authenticates to nothing.
- Local `local/build-local.sh` was not used: it needs entitlement material, which this run did not handle.
- **Open:** the owner approves or changes this plan.
