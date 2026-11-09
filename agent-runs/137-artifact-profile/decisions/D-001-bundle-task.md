# D-001 A new `box1-maven-bundle` Task, not a step in `box1-quarkus-maven`

**Decision.** New cluster Task `box1-maven-bundle` (box1-gitops `platform/pipelines/tasks/maven-bundle.yaml`): fetch → multi-module `mvn verify -DskipITs=false` → stage and OCI layout (Python, builder image) → unprivileged `skopeo copy --preserve-digests --digestfile` (pinned `ubi9/skopeo@sha256:fd3d5c37…`, skopeo 1.22.2) to `registry.apps.ocp.box1.org/box1-ci/<repo>-bundle:<revision>`. The push fails unless the pushed digest equals the built layout digest. PRs use the same Task with `push-image: 'false'` (packaged, not pushed).

**Why.** Keeps `box1-quarkus-maven` byte-identical for services (pinned by hash in `test-maven-bundle.py`); a step after it would still need its own image (no skopeo in `box1-builder`, checked in `box1-build/builder/Containerfile`) and would re-fetch the source. Building the bundle in PRs too catches a module without a fast-jar before merge.

**Discovery.** `box1-builder` has Maven 3.9.16, Python 3.11, syft, roxctl, no skopeo. `registry.apps.ocp.box1.org` presents a publicly trusted certificate (same route Jib pushes to).
