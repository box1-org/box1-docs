# D-005: Database credential while #41 is open

- **Status:** open (O-11).
- **Finding:** the scaffold's PostgreSQL credential follows the template pattern tracked in [#41](https://github.com/box1-org/box1-docs/issues/41). Details were reported to the user directly, not here, because this repository is public.
- **Run behavior until decided:** no credential was read or used. Local tests use throwaway containers.
