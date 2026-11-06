# D-011 Deterministic seed fixtures and reset

**Status:** fixtures decided. **Creating them on the cluster needs approval (O-6).**

- **Synthetic identities:** customers `cust_demo_ada`, `cust_demo_lin` and `cust_demo_kai`. Sites and SKUs are taken from the inventory service's seeded stock (read at runtime and listed in `docs/demo-walkthrough.md`).
- **Fixture orders:** the walkthrough creates them through the console (operator role) with idempotency keys `demo-<scenario>-<n>`. Repeating a key replays the same order and allocates nothing new.
- **Reset:** order-service has no delete or cancel endpoint ("No v1 endpoint performs it"). Fixtures are therefore **additive and never deleted**. A fresh demo run uses a new key series (`demo-<scenario>-<date>-<n>`). No other data is touched.
- **Local tests** use stubs and a local Keycloak and touch no cluster data.
