# D-005 Live database credential

**Status:** resolved 2026-11-05 by the user: option B, add a secrets integration first. Which integration is open as D-016. Still blocks Phase 6.

**Finding:** the database credential for `order-service-dev` does not meet `postgres/SECRETS.md`, and real order data should not be deployed on it. The specifics were given to the user directly and are deliberately not recorded here, because `box1-docs` is public.

To re-check, compare the password keys of Secret `order-service-postgres` with `workloads/order-service/postgres.yaml` in `box1-workloads-dev`. Record only whether they match, never a value.

Because the Secret is declared in Git and the Application has `selfHeal: true`, Argo CD should revert a manual change to it. That revert was not tested. No ExternalSecret, SealedSecret or Vault CRD is installed. The namespace has no NetworkPolicy.

**Options:**

- **A (recommended): remove the Secret from Git and provision it out of band.** A `box1-workloads-dev` PR removes the manifest, the user creates the Secret outside Git, and the PostgreSQL role password is rotated. Add a NetworkPolicy for port 5432. Removal must be checked against Argo's prune behavior so the Secret is not deleted.
- **B: add a secrets integration first.** Cleaner, but it is new shared infrastructure outside this prompt.

**Wider issue:** the Secret manifest comes from the template, so other services onboarded with PostgreSQL should get the same check. No backlog issue was filed, because filing was not requested.
