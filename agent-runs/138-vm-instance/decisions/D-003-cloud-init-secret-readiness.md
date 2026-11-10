# D-003 Readiness check for the `<instance>-cloud-init` Secret

**Options considered** (from #140):
- (a) `get` on that single Secret name, requested as `PartialObjectMetadata`;
- (b) rely on the VM failing to start.

**Chosen: (a).** The requirement is to "keep the VM Halted with a clear message". Option (b) starts the VM, so it cannot meet that.

How it works:
- The bundle's `onboarding.yaml` adds Role `<instance>-cloud-init-observer`: `get` on `secrets`, `resourceNames: [<instance>-cloud-init]`. It is bound to `rhdh/developer-hub-onboarding`.
- The plugin sends `Accept: application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1`. If the server ignores `as=`, it refuses the response rather than keep it (fail-closed).
- The check also requires the labels that the #140 assembly script sets.
- Until the Secret exists, platform readiness reports "create it with box1-docs runbooks/vm-cloud-init-identity.md (approval required)…". Promotion is refused and the VM stays Halted. Resubmitting resumes.

**Tradeoff:** RBAC cannot grant metadata-only access, so the Hub *could* read that one credential. The Hub already holds `get/create/update/delete` on Secrets in `box1-ci`.

**Not done:** no Secret was created; creating one is an approval item. The live behaviour has not been observed.
