# Platform change during the run: the adapter reaches the ERP VM

Observed 2026-11-06 ~02:00 EST, read-only. Not this run's change.

- box1-workloads-dev `ea57006` "legacy-erp SFTP endpoint and adapter SFTP enablement", merged as #100 (`a5e472c`, 01:07 EST).
- Live: Service `legacy-erp-sftp` (ClusterIP, 22/TCP) in `legacy-erp-dev`; the adapter Deployment has `FULFILLMENT_SFTP_ENABLED=true`,
  `FULFILLMENT_SFTP_HOST=legacy-erp-sftp.legacy-erp-dev.svc`. Argo `fulfillment-adapter` and `legacy-erp` Synced/Healthy at `a5e472c`.
- Adapter log at 06:10:57Z: "Uploaded request file: reason=FIRST", then "Applied ERP result: revision=1 status=PENDING".

Effect on `evidence/01-mechanism-classification.md`: **P-3 is superseded.** Guided ERP scenarios can now be observed through
the adapter on the cluster. `erp-manual-hold` needs no demo faults; `erp-delayed-processing` and `erp-crash-after-commit`
still need P-4 (`faults = true` in the VM), which was not checked inside the VM (no access issued to this run).
