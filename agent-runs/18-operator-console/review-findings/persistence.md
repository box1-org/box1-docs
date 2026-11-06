# Review pass: Persistence (architecture subagent)

**Not applicable, with evidence.**
- No datasource, JDBC, ORM, Flyway or Liquibase in `pom.xml`. The only Hibernate artifact is the validator.
- No SQL or migration files.
- The session is an encrypted OIDC cookie with no server store.
- The only in-process state is the 60 s `/api/info` cache, which holds successes only and is lost on restart, harmlessly.

Findings: none.
