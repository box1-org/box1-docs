# D-002 Source annotation name

**Decision:** an instance records its source on the VirtualMachine in the metadata annotation `box1.org/source-image: <source-repo>`.
- It sits beside `box1.org/os-image-digest`.
- The value is the bare repository name, which must be on the allowlist (D-001).
- The validator requires the annotation exactly once.
- `box1-gitops-promote` refuses to promote an instance whose annotation differs from `application-name`.
