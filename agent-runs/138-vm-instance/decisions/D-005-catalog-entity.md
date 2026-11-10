# D-005 Catalog entity

**Decision:** each instance is a `Component`:
- `component:default/<instance>`, `spec.type: vm-instance`, `lifecycle: experimental`;
- `dependsOn: component:default/<source>`;
- annotations for Kubernetes and Argo CD, plus `box1.org/source-image` and `box1.org/site-id`.

It is defined in `box1-workloads-dev/workloads/<instance>/catalog-info.yaml`, which `kustomization.yaml` does not list. The catalog Location target is that file.

The new optional table key `catalogEntity` supplies `ref`, `target` and the ownership test. An existing entity is reused only if it is a `vm-instance` Component managed by that Location. The completion predicate additionally requires the booted digest to equal the adopted digest.

**Why Component rather than Resource:** the instance shows Kubernetes and Argo CD status like other workloads. Name collisions with repositories are refused when the source is resolved.
