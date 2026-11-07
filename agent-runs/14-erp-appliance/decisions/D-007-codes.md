# D-007 Status, error and rejection codes

- Result status: `PENDING`, `HELD`, `SHIPPED`, `REJECTED`.
- Rejection reason codes (operator chooses one, plus required free text): `STOCK_UNAVAILABLE`, `SITE_UNAVAILABLE`, `DAMAGED_GOODS`, `OPERATOR_CANCELLED`, `OTHER`. They match `shipment.failed.v1`'s `reasonCode` pattern so the adapter can pass them through; reason text never goes into events.
- Inbound error codes: `ENCODING`, `MALFORMED_RECORD`, `UNSUPPORTED_VERSION`, `MISSING_FIELD`, `FIELD_LENGTH`, `FIELD_VALUE`, `RECORD_ORDER`, `TRUNCATED`, `COUNT_MISMATCH`, `FILENAME_MISMATCH`, `FILE_TOO_LARGE`, `CONFLICTING_REUSE`.
