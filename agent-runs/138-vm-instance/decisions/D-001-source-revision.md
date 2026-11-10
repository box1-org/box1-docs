# D-001 `sourceRevision` semantics

**Decision:** An instance's `sourceRevision` is the source's approved revision. That is `box1.org/source-revision` in `box1-workloads-dev` `workloads/<source>/virtualmachine.yaml` on `main` at the time of the request. `box1:development:resolve-source` reads it before the bundle is rendered. `provision` reads it again and refuses with "submit the template again" if it changed in between. Nothing is recorded in that case.

**Resume behaviour:** once a request has a record, `resolve-source` returns the recorded revision. A later source release therefore never changes an instance that is still being onboarded.

**Why:** the prompt proposed this semantics. It keeps the plugin's existing checkpoint, which binds every phase to one 40-hex `sourceRevision`.
