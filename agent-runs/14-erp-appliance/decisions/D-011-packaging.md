# D-011 Artifact packaging, pinning and install layout for #25

- Pure-Python package `box1_erp`, **standard library only** at runtime (`sqlite3`, `curses`), targeting RHEL 10's system Python 3.12. No pip downloads at boot or in the image beyond the wheel itself.
- Artifact: `box1_ops_erp_simulator-<version>-py3-none-any.whl` + `SHA256SUMS` + `systemd/` units + `config/erp.conf.example`, published as an OCI image by digest (D-002). Until CI exists, the same bundle is built locally and its sha256 recorded.
- Install layout in the guest: `python3 -m venv --system-site-packages /usr/lib/box1-erp/venv` and `pip install --no-index --no-deps <wheel>` at image build time; units in `/usr/lib/systemd/system/`; config `/etc/box1-erp/erp.conf`; state on the data volume at `/var/lib/box1-erp` (`ledger.db`, `spool/{archive,quarantine}`, `backups/`); exchange at `/srv/box1-erp/exchange/{inbound,outbound,consumed}` on the same data volume.
- Users: `box1erp` (worker and TUI, owns ledger and spool), `erpsftp` (SFTP only, chrooted to `/srv/box1-erp/exchange`, no access to `/var/lib/box1-erp`). Shared group `erpxfer` on `inbound`/`outbound`/`consumed`.
- #25 owns `box1-erp.target`, console selection, mounts and `sshd` config; this repo ships the two application units and documents the mount requirement (`RequiresMountsFor=/var/lib/box1-erp /srv/box1-erp`).
