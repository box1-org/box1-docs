#!/bin/sh
# Run the #14 ERP (box1-org/box1-ops-erp-simulator) as this run's SFTP test partner, with run13-* names only.
# Usage: erp-harness.sh start|stop|mode AUTO|MANUAL|ship ID|hold ID|release ID|reject ID CODE|reemit ID|faults on|off|fault KEY VALUE|ledger|rekey
# Test-only: run against the local run13-erp container. WORK holds a throwaway client key and known_hosts; it is a scratch directory, never committed.
set -eu
NAME=run13-erp; VOL=run13-erp-data; IMAGE=localhost/run13-erp-harness:dev; PORT=${PORT:-22213}
WORK=${WORK:?set WORK to a scratch directory}
x() { podman exec "$NAME" "$@"; }
# Values travel as environment variables (A1, A2), never inside the Python source, so arguments cannot inject code.
asapp() { podman exec -u box1erp -e BOX1_ERP_CONFIG=/etc/box1-erp/erp.conf -e "A1=${2:-}" -e "A2=${3:-}" "$NAME" \
  /usr/lib/box1-erp/venv/bin/python -c \
  "import os; from box1_erp import config, db, domain; c=db.connect(str(config.load().ledger)); A1=os.environ['A1']; A2=os.environ['A2']; $1"; }
hostkey() {  # known_hosts from the container's own public key file, out of band; never from a network scan
  printf '[127.0.0.1]:%s %s\n' "$PORT" "$(x cat /etc/ssh/ssh_host_ed25519_key.pub | cut -d' ' -f1-2)" > "$WORK/known_hosts"; }
case "$1" in
start)
  mkdir -p "$WORK"
  echo "clocks: host $(date -u +%H:%M:%S) podman-vm $(podman machine ssh date -u +%H:%M:%S | tail -1)"
  podman volume create "$VOL" >/dev/null
  podman run -d --name "$NAME" --systemd=always --memory 512m -p "127.0.0.1:$PORT:22" \
    --mount "type=volume,src=$VOL,dst=/srv/box1-erp" "$IMAGE" >/dev/null
  n=0; until x systemctl is-system-running 2>/dev/null | grep -qE 'running|degraded'; do n=$((n+1)); [ $n -gt 60 ] && exit 1; sleep 1; done
  x /usr/libexec/box1-erp/provision-data-volume.sh --init-ledger >/dev/null
  x systemctl reset-failed box1-erp-worker; x systemctl start box1-erp-worker
  rm -f "$WORK/id_ed25519" "$WORK/id_ed25519.pub"
  ssh-keygen -q -t ed25519 -N '' -C run13-harness-only -f "$WORK/id_ed25519"
  podman cp "$WORK/id_ed25519.pub" "$NAME:/etc/ssh/authorized_keys/erpsftp"; x chmod 0644 /etc/ssh/authorized_keys/erpsftp
  hostkey; echo "ERP running on 127.0.0.1:$PORT; worker $(x systemctl is-active box1-erp-worker)";;
stop) podman rm -f "$NAME" >/dev/null; podman volume rm -f "$VOL" >/dev/null;;
mode) asapp "domain.set_mode(c,A1,actor='console',label='run13')" "$2";;
ship) asapp "print(domain.ship(c,A1,expected_version=None,actor='console',label='run13'))" "$2";;
hold) asapp "domain.hold(c,A1,expected_version=None,actor='console',label='run13',reason='run13 hold')" "$2";;
release) asapp "domain.release(c,A1,expected_version=None,actor='console',label='run13')" "$2";;
reject) asapp "domain.reject(c,A1,expected_version=None,actor='console',code=A2,reason='run13 operator note: do not copy',label='run13')" "$2" "$3";;
reemit) asapp "domain.reemit(c,A1,actor='console',label='run13')" "$2";;
faults) v=false; [ "$2" = on ] && v=true; x sed -i "s/^faults = .*/faults = $v/" /etc/box1-erp/erp.conf; x systemctl restart box1-erp-worker;;
fault) asapp "domain.set_fault(c,A1,A2,demo_enabled=True,actor='console',label='run13')" "$2" "$3";;
ledger) x sqlite3 /srv/box1-erp/state/ledger.db "SELECT request_id,state,shipment_id,version FROM requests ORDER BY request_id";;
rekey) x sh -c 'rm -f /etc/ssh/ssh_host_*; ssh-keygen -A >/dev/null; systemctl restart sshd';;  # new host key; known_hosts NOT updated
trust) hostkey;;
*) echo "unknown command" >&2; exit 2;;
esac
