# D-009 Output schema, citations and failure mapping

**Status:** proposed.

- The model returns `{summary, findings[{statement, evidenceRefs[], confidence: LOW|MEDIUM|HIGH}], unknowns[], suggestedActions[{type, description, expectedEffect, rollback}]}`.
- **Validation in the service, after decoding:**
  - The JSON must parse and match the schema. If not, the status is `MODEL_INVALID_OUTPUT`, with no findings shown; the raw text is not stored.
  - A `finish_reason` of `length` is treated as truncated and gets the same status.
  - A finding with no `evidenceRefs`, or refs that do not exist, is dropped and counted in `unsupportedAssertions`.
  - A suggested action whose `type` is not in the allowlist (D-011) is dropped and counted.
  - A model refusal, or empty findings, is a valid `COMPLETED` result with `unknowns`.
- Every unavailable evidence source is added to `unknowns` by the service, not by the model.
