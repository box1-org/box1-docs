# D-001 Repository and front-end build

**Status:** decided. Proven in CI (evidence/01).

- **Repository:** `box1-org/operations-console`, onboarded by the user through the Golden Path (namespace `operations-console-dev`). The prompt's `box1-ops-console` was only a proposal.
- **Front end:** `src/main/webui/`.
  - Libraries: React 19.3, react-router 7, **react-aria-components** as the accessible component library (unstyled, so it fits the monochrome brand), Vite 8 and TypeScript 7.
  - Versions are exact. `package-lock.json` is committed, and `.npmrc` sets `ignore-scripts`, `engine-strict` and `update-notifier=false`.
- **Node:** v24.22.2 LTS. It is fetched by `download-maven-plugin` with a pinned SHA-256 per OS profile and installed by `frontend-maven-plugin` 2.0.2 from the verified local file.
  - Quinoa was rejected. It adds a Quarkus extension whose release cadence must track the Golden Path's platform BOM, and it uses the same unverified Node download.
- **Packaging:** Vite writes `target/webui-dist`, which Maven copies to `META-INF/resources`.
- **Serving:**
  - `/assets/*` names are content-hashed and sent with `Cache-Control: public, max-age=31536000, immutable`.
  - `index.html` is sent with `Cache-Control: no-store`.
  - **SPA fallback:** a GET for any path that is not `/api/*`, `/q/*` or `/assets/*`, has no file extension, and accepts `text/html` is served `index.html`. API and `/q` 404s stay 404s.
- **Shared tasks:** no change to `box1-quarkus-maven` or the smoke task.
