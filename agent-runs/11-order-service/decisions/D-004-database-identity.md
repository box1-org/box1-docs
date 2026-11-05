# D-004 Database and login names

**Status:** open, user decision. Blocks Phase 2 and the migration plan. Applies if D-001 selects `order-service`.

**Conflict:** `postgres/OWNERSHIP.md` assigns database `box1_order` and login `box1_order_app`, and says the runtime login must not own the schema. The template deployed database `order_service` with login `order_service`, a single login that would own its schema. The template names every service's database this way, so the conflict will recur for later services.

**Options:**

- **A (recommended): keep the generated names and amend `OWNERSHIP.md` by pull request.** Add a mapping and keep the isolation rule. No change to the live database.
- **B: change the deployment to `box1_order` / `box1_order_app`.** Matches the contract as written, but the running database was initialized with the old names, so it needs either a recreated volume or new roles. Anything touching persistent data needs separate approval.

A separate migration owner is a design question under either option. `OWNERSHIP.md` requires it only "when the deployment supports it", and it would need one more credential.
