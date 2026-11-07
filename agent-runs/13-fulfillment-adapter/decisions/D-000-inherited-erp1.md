# D-000 Inherited ERP1 decisions from #14

**Status:** binding input, read from `origin/agent-run/14-erp-appliance` (`e48e036`) on 2026-11-05. Not decided by this run.

| #14 decision | Binding rule for the adapter |
|---|---|
| D-003 protocol location | ERP1 lives in `box1-ops-contracts/legacy/erp-file/v1/`; the adapter pins a commit (`eef13ea`) and never copies spec or fixtures. |
| D-004 line items | One `fulfillment.requested.v1` → exactly one `LIN` (lineNo 1). A file carries 1–99 `LIN`. |
| D-005 equivalence | Identity is `fulfillmentRequestId`; equivalence compares orderId, reservationId, siteId and ordered lines only. Equivalent repeat → ERP republishes latest result; non-equivalent → `CONFLICTING_REUSE` ERR. |
| D-006 results | Revisions 1, 2, 3…, `rsl_` IDs, re-emission reuses name and bytes; order by revision, never filename or arrival; terminal is highest. |
| D-007 codes | Statuses PENDING/HELD/SHIPPED/REJECTED; rejection codes pass through to `shipment.failed.v1`; reason text never in events; 13 error codes incl. `UNREADABLE`. |
| D-009 durability | Adapter uploads `.tmp` then renames; ERP relies on `TRL` count; ERP may republish the same name and bytes after a crash. |
| D-011 packaging | SFTP user `erpsftp`, chroot is the exchange (`/inbound`, `/outbound`, `/consumed`). |
| D-013 encoding | UTF-8 no BOM, LF only, no control characters, `\|` and `\\` escapes only, code-point lengths. |
