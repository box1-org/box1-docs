# Front-end build in the Golden Path pipeline (Phase 0 probe)

**Result: the unmodified `box1-quarkus-maven` task builds a React/TypeScript front end from a pinned lockfile.** Proof level: `ci_verified` (real PR pipeline on the cluster).

- Probe PR: box1-org/operations-console#1 (draft, do not merge), head `ae245e774fecf904c0fda93cdf67b708eb22b1ac`.
- PipelineRun `box1-ci/operations-console-validate-zqk5s`: Succeeded in 1m17s (2026-11-05 ~22:53 EST).
- No change to the shared task, the smoke task or any other repository.

## How the build works

| Step | Mechanism |
|---|---|
| Node | `download-maven-plugin` 2.1.0 fetches `node-v24.22.2-<platform>.tar.gz` from nodejs.org and checks it against the SHA-256 in that release's SHASUMS256.txt, pinned in `pom.xml` per OS profile (`linux-x64`, `darwin-arm64`) |
| Install | `frontend-maven-plugin` 2.0.2 installs Node from that verified file (`nodeDownloadRoot=file://target/node-mirror/`). The plugin itself does not verify checksums, which is why the download step comes first. |
| Packages | `npm ci` from the committed `package-lock.json` against `registry.npmjs.org`. `.npmrc` sets `ignore-scripts=true`, `engine-strict=true` and `save-exact=true`. |
| Build | `tsc --noEmit`, then `vite build` into `target/webui-dist`, which Maven copies to `META-INF/resources` |
| Test | `FrontendServedTest` (`@QuarkusTest`) asserts that `/` serves the built `index.html` |

## Observed in the pipeline log (excerpt)

```
[INFO] --- download:2.1.0:wget (fetch-verified-node) @ operations-console ---
[INFO] Installing node version v24.22.2
[INFO] Downloading file:///workspace/application/target/node-mirror/v24.22.2/node-v24.22.2-linux-x64.tar.gz ...
[INFO] Installed node locally.
[INFO] Running 'npm ci --no-audit --no-fund' in /workspace/application/src/main/webui
[INFO] added 24 packages in 1s
[INFO] vite v8.3.6 building client environment for production...
[INFO] ../../../target/webui-dist/assets/index-ByNGCpvJ.js  220.15 kB │ gzip: 68.89 kB
[INFO] Copying 2 resources from target/webui-dist to target/classes/META-INF/resources
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 ... in org.box1.FrontendServedTest
[INFO] BugInstance size is 0
[INFO] BUILD SUCCESS
```

- The bundle hash `index-ByNGCpvJ.js` is identical to the local macOS build, so the output is reproducible across platforms.
- npm printed an update notice on stderr, which the plugin logs as `[ERROR]`. It is harmless and will be silenced with `update-notifier=false`.

## Negative check (local)

`./mvnw initialize -Dnode.sha256=000…0` fails with `Not same digest as expected: expected <000…> was <aa9549…385a>`. The pin is enforced.

## Implications

- Build pods reach nodejs.org and registry.npmjs.org: `box1-ci` has no NetworkPolicy, EgressFirewall or proxy. This is observed, not guaranteed. If egress is later restricted, the build breaks loudly, not silently.
- On a release, the task runs the front-end build twice (`verify`, then `package` for Jib). That costs seconds.
- PaC reads pipeline definitions from `main`. The probe used the template's unchanged `.tekton/`, so the result carries over to the real PR.
