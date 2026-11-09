# D-002 Bundle layout

**Decision.** One `FROM scratch` layer:

```text
/<module>/quarkus-app/...   each <module> of the root pom.xml <modules>, in order (Quarkus fast-jar)
/SHA256SUMS                 sha256 of every file above, sorted, "./<path>"
```

Entries sorted, mtime 1980-01-01, uid/gid 0, modes 0755/0644, symlinks refused, gzip mtime 0. OCI labels/annotations: `org.opencontainers.image.revision`, `.source`, `.title`, `org.box1.bundle.modules`, `org.box1.bundle.layout`. Module names `^[a-z][a-z0-9]{1,19}$` (no Java keywords, not `config`, `docs`, `target`, `src`).

Consumer usage: `COPY --from=<registry>/box1-ci/<repo>-bundle@sha256:<digest> / <path>`, then `java -jar <path>/<module>/quarkus-app/quarkus-run.jar`.

**Agreement with `site-gateway-os`.** That repository does not exist yet (checked 2026-11-08, `gh api repos/box1-org/site-gateway-os` → 404), so the layout could not be agreed with its Containerfile. #126 must create it with exactly one such COPY line. Verified locally instead: a consumer Containerfile copying the digest ran `gateway` (evidence/local-maven-bundle.md).

**Reproducibility.** The parent POM sets `project.build.outputTimestamp`; two independent local builds gave the same digest `sha256:3037ddca…`. Not yet observed in the cluster.
