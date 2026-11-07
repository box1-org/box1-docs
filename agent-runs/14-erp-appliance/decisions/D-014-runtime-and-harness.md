# D-014 Development runtime and test harness

- Develop and test on Python 3.12 (`uv`-managed, matching RHEL 10), not the workstation's system 3.9.
- Unit and fixture tests: `pytest` on the host, real SQLite files in temp directories, real subprocesses for worker/TUI independence, a pseudo-terminal for 80x24 rendering.
- Container harness: `quay.io/centos/centos:stream10` (closest public image to RHEL 10: Python 3.12, OpenSSH, systemd), containers named `run14-*`, real `sshd` with an SFTP-only chrooted account to prove the database is unreachable. It does not replace VM acceptance.
- Dev-only dependencies: `pytest`, `ruff`, `build`, pinned in `requirements-dev.txt`.
