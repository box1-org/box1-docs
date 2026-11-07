# D-012 Database identity and credential

**Status:** decided by the agent for names. Credential position is the user's existing decision in the order run (D-005, D-016, box1-docs#41).

- **Names:** database and login `inventory_service`, as generated. `postgres/OWNERSHIP.md` already says generated names replace its table, so a contracts PR adds one line stating the mapping. The isolation rule stays: separate PostgreSQL instance per service, separate Secret and a NetworkPolicy on 5432.
- **One login** runs migrations and queries, as Order does, because the deployment has one. A separate owner is a recorded limitation to revisit with #41.
- **Credential:** this service has the same inline-Secret arrangement described in the order run's D-005, from the same template. Details were reported directly to the user. To re-check: compare the Git manifest and Secret annotations per order run D-005, with the user's approval. This run did not read the cluster Secret.
- **Isolation test:** the network and instance separation are visible in manifests. The negative login test in `OWNERSHIP.md` needs credentials not issued to this run, so it stays not tested live.
