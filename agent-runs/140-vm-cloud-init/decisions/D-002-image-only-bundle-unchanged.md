# D-002 The parameter changes the image only; the template's GitOps bundle is unchanged

- **Decision:** with `cloudInit: true`, only the OS image definition changes (`Containerfile`, `README.md`, and the added `rootfs-cloud-init/` tree). The template's own VM has no NoCloud disk and boots with the `None` datasource.
- **Why:** the per-instance disk belongs to `vm-instance` bundles (#138), which have their own identity. Keeping the `virtual-machine` bundle unchanged means `validateVmBundle` (`plugins/box1-onboarding/workflow.cjs`, being refactored in #136) and `gitops-validate` (#139) need no change for this template. It also makes the source repository's own VM the proof that an image with cloud-init boots without a NoCloud disk.
- **Consequence:** #138 adds the `cloudinitdisk` disk/volume and the `<instance>-site` ConfigMap to `vm-instance` bundles; #139 adds the validator rules (runbook, "Instance bundle specification").
