# D-005 Regression service and VM names (proposed)

**Proposed, not used:** `regress136-svc` (Quarkus service, template `quarkus-rest-service`) and `regress136-vm` (RHEL image mode VM, template `rhel-image-vm`). Both pass `validateName` and are unused (no `rhdh/box1-onboard-*` record with these names at discovery).

Live onboarding creates repositories and deploys, so it needs the user's approval after the 1.3.0 digest is live. Decommission both afterwards per `runbooks/service-decommission.md` (VM extras: DataVolume/root PVC, `<name>-disk` ImageStream, puller RoleBinding in box1-ci) unless the user keeps them as references.
