# D-004: Scenario mechanisms (proposed; awaiting the user's review)

- **Status:** accepted by the user, 2026-11-06 ("1 - thats fine").
- **Proposal:** the classification in `evidence/01-mechanism-classification.md`:
  - service API: `baseline-order`, `inventory-contention`, `red-alert`;
  - guided ERP console step: `erp-manual-hold`, `erp-delayed-processing`, `erp-crash-after-commit`, plus ERP shipping inside `baseline-order`;
  - VM-level: `erp-unavailable`;
  - platform-level: `broker-outage`, `poison-event`;
  - not yet possible as written: `bad-artifact-gate`.
- On the cluster today no scenario runs end to end; the blockers are P-1 to P-6.
