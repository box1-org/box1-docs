# D-010 Untrusted data and prompt injection

**Status:** proposed.

- The system policy is fixed in code and versioned. Evidence goes into a single user message as JSON with explicit `untrusted` framing; nothing from evidence is ever placed in the system message.
- Injection cannot gain capability for three reasons:
  - the model has no tools (D-006);
  - the service, not the model, decides what evidence is fetched;
  - output is schema-validated and citation-checked (D-009).
- The most an injection can achieve is a misleading summary. Citation checks and the evaluation set measure that risk.
- Evidence beyond the incident's own order or asset is never fetched, so an injection cannot widen what is disclosed.
- **Tests:** injection strings in order notes or fields, Kafka payload text fields, and a fake runbook reference. The expected result is no extra calls, no extra data and an unchanged role decision.
