# Operator console mockup (box1-docs#18)

Static, clickable discussion mockup of the **box1 Operations** console. It has no build step, no backend and only synthetic data. It is not the implementation; the issue calls for TypeScript/React in `box1-org/box1-ops-console`.

```sh
cd box1-docs/mockups/operator-console
python3 -m http.server 8088   # then open http://localhost:8088 (Safari or VS Code preview)
```

Opening `index.html` directly via `file://` also works.

- `CAPABILITIES.md` lists the functional capabilities (C1–C15), the role matrix, the walkthrough and the open gaps.
- The ribbon at the top (mockup-only) switches role and simulates loading, empty and error data states.
- Buttons with dashed borders simulate backend events and are not product features.
- Files:
  - `index.html` and `app.js`: shell and hash router
  - `mock.css`: brand tokens copied from `run15-asset-service`
  - `mock-data.js`: synthetic fixtures
  - `brand/box1-mark.png`: copied from `run15-asset-service`, decision D-016
