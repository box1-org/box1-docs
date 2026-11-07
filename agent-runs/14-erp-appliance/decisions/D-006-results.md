# D-006 Result identity, revisions and ordering

- Every business-state change of a request (import → PENDING, HELD, release → PENDING, SHIPPED, REJECTED) creates one result with a new revision: 1, 2, 3… per request, assigned in the same transaction as the state change.
- Result ID: `rsl_` + 32 lowercase hex, random, stored with the revision. Its bytes are stored in the ledger at creation; re-emission publishes the stored bytes, so identity and content are preserved exactly.
- Ready file name: `RES.<fulfillmentRequestId>.<revision, 6 digits>.<resultId>.erp1`. Re-emission reuses the name.
- Consumers order by revision, never by file name or arrival; a lower or equal revision than the one held is a duplicate or late result and must not regress state. `SHIPPED`/`REJECTED` are terminal and are always the highest revision.
- Inbound rejections are `ERR` files (`err_` + 32 hex), outside the revision stream, because they do not change the request's state.
