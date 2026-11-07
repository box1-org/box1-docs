# Architecture pass

Reviewed `9d6deed` by reading code. A fresh agent, given the diff, prompt and contracts. No high findings.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| M1 | Medium | Expiry ignores consumer lag. A signal dead-lettered in a long database outage, a pod down past the TTL, or a broker outage sends a healthy order to `EXCEPTION`. | **Fixed, partly.** `ExpiryGate` holds expiry after startup, during and after retries, after late events, and while the broker is unreachable. Availability errors no longer dead-letter. **Remains:** a reservation unpublished past its `expiresAt` still goes to `EXCEPTION` by Order's own rule. Documented in the runbook. |
| M2 | Medium | A late shipment reduces `on_hand` again per delivery. | **Fixed.** At most one adjustment per hold, with a unique index. Test added. |
| M3 | Medium | Operator release tells Order nothing, and the runbook said Order goes to `EXCEPTION`. | **Runbook corrected.** The gap stays, because no contract event exists. Follow-up. |
| L1 | Low | A shipment is not checked against the committed `fulfillmentRequestId`. | **Fixed.** Opens `SHIPMENT_REQUEST_MISMATCH`, and moves nothing. |
| L2 | Low | A permanent failure does not keep an `ACTIVE` hold, despite the comment. | **Comment and runbook corrected** to match D-005's intent for `COMMITTED` only. |
| L3 | Low | History could record a stale `from_status`. | **Fixed.** The row is locked before reading. |

Also confirmed: the first-start policy, boundaries, event compatibility, publish order, one outcome per order and no lock cycle. The reviewer pointed out `COMMITTED` holds have no exit today, which matters for how many live orders run.
