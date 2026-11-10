# D-003 How catalog actions find the profile

**Decision.** `box1:catalog:submit|verify|ensure` keep their `{name}`-only input schema. `registerCatalog` evaluates `PROFILES[record.profile || 'service'].catalogComplete(record)`; the Workflow's own input profile (always the default `service` for catalog actions) is not used. A record without `profile` is a service, as before.

**Why.** Existing templates keep working without change; the stored record is the authority every other phase already checks against; the Hub action schemas stay identical.

**Consequence.** `catalogSubmit`/`catalogVerify` do not consult the profile (unchanged from 1.2.0). A profile with no source repository (#138) needs a catalog-target handler or optional catalog input, decided in that run.
