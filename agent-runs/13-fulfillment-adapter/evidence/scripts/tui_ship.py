#!/usr/bin/env python3
"""Ship one request through the real ERP TUI (curses, 80x24) in run13-erp by keystrokes, then check the adapter.

Usage: WORK=<scratch> python3 -I tui_ship.py   (adapter running on :28080, ERP in MANUAL mode)
Keys: "/" + request ID + Enter (find), "s" (ship), "Y" (confirm), exactly as an operator types them.
"""
import fcntl, json, os, pty, re, select, struct, subprocess, sys, termios, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenarios as sc  # noqa: E402  (shared helpers; its main() does not run on import)

fid, oid, body = sc.ids('tui')
code, _, _ = sc.http('POST', '/api/fulfillments', body, headers={'X-Correlation-ID': f'corr-{fid}'})
sc.check('tui: REST accepted', code == 202)
sc.check('tui: ERP imported and acknowledged (PENDING)', sc.wait('', sc.outcome(fid, 'PENDING'), 30))

pid, fd = pty.fork()
if pid == 0:
    os.execvp('podman', ['podman', 'exec', '-it', '-u', 'box1erp', '-e', 'BOX1_ERP_CONFIG=/etc/box1-erp/erp.conf',
                         '-e', 'TERM=vt220', '-e', 'LINES=24', '-e', 'COLUMNS=80', 'run13-erp', '/usr/bin/box1-erp', 'tui',
                         '--label', 'run13-tui'])
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
screen = b''


def pump(seconds):
    global screen
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                screen += os.read(fd, 65536)
            except OSError:
                return


def keys(text, pause=0.6):
    for ch in text:
        os.write(fd, ch.encode())
        time.sleep(0.15)
    pump(pause)


pump(4)
keys('/' + fid + '\r', 1.5)
keys('s', 1.0)
keys('Y\r', 3.0)
plain = re.sub(rb'\x1b\[[0-9;?]*[A-Za-z]|\x1b[()][A-Z0-9]|\x1b[=>]', b' ', screen).decode('ascii', 'replace')
shipped_msg = re.search(r'Shipped (ful_\S+) as (shp_[0-9a-f]+)', plain)
subprocess.run(['podman', 'exec', 'run13-erp', 'pkill', '-f', 'box1-erp tui'], capture_output=True)
try:
    os.kill(pid, 9)
except ProcessLookupError:
    pass
sc.check('tui: operator keystrokes shipped the request in the TUI', shipped_msg is not None and shipped_msg.group(1) == fid,
         shipped_msg.group(0) if shipped_msg else plain[-300:].replace('\n', ' '))
shp = shipped_msg.group(2) if shipped_msg else None
audit = sc.sh('podman', 'exec', 'run13-erp', 'sqlite3', '/srv/box1-erp/state/ledger.db',
              f"SELECT actor_type, actor_label FROM audit WHERE action = 'SHIP' AND request_id = '{fid}' ORDER BY rowid DESC LIMIT 1")
sc.check('tui: ERP audit records the console actor and TUI label', audit == 'console|run13-tui', audit)
sc.check('tui: adapter applied SHIPPED from the ERP result', sc.wait('', sc.outcome(fid, 'SHIPPED'), 30))
ev = sc.wait('', lambda: sc.events(fid), 30) or []
sc.check('tui: one shipment.confirmed.v1 carrying the TUI shipmentId', len(ev) == 1 and ev[0]['payload']['shipmentId'] == shp
         and sc.status(fid)['shipmentId'] == shp, str(shp))
passed = sum(1 for _, ok in sc.RESULTS if ok)
print(f'== {passed}/{len(sc.RESULTS)} checks passed')
sys.exit(0 if passed == len(sc.RESULTS) else 1)
