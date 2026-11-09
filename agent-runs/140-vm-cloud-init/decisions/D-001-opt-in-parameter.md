# D-001 `cloudInit` is an opt-in template parameter (default `false`)

- **Decision:** `rhel-image-vm` gets a boolean parameter `cloudInit`, default `false`. The conditionals test `values.cloudInit === true`, so anything other than boolean `true` renders off.
- **Why:** repositories generated without it stay byte-identical (proven against `origin/main` by `VM_BASELINE_REF=origin/main npm run validate`). Most VMs (`legacy-erp`, `vm-golden-check`) have one identity and gain nothing from cloud-init.
- **Not taken:** default on. It would add a package, boot stages and a new trust input to every new VM.
