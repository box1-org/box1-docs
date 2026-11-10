# D-003 Promote instance parameter

**Decision:** `box1-gitops-promote` gains the param `instance-name` (string, default `''`).

**When `workload-profile: vm-instance`:**
- `instance-name` is required.
- `application-name` stays the **source** repository: supersession checks use `box1-org/<application-name>` main.
- After the supersession setup, the script sets `name` to the instance. So the candidate files (`workloads/<instance>/`), branch, PR title and Argo sync target all use the instance.

**For other profiles:** `instance-name` must be empty (assert), so a misconfigured caller fails loudly.

**Existing callers:** the box1-templates `quarkus-rest-service` and `rhel-image-vm` skeletons, `vm-golden-check`, and `legacy-erp` `release.yaml` and `appliance-pipeline.yaml`. None passes it; checked by grep on 2026-11-08.

**For #138:** `box1-vm-smoke` and `box1-bootc-apply` treat `application-name` as both the Argo Application and the VM name. An instance release passes the instance name to them.
