# D-008 SFTP test server

**Status:** decided by the agent in Phase 1, 2026-11-05.

**Decision:** local only. The #14 ERP harness, built from a clone of `run14-erp` at `f15513c` and run as `run13-erp`, is the SFTP server and test partner for every scenario. No in-cluster SFTP test endpoint is requested; that would need approval and adds nothing the harness cannot show before the VM exists.
