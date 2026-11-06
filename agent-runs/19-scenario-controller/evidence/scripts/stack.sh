#!/bin/sh
# Local end-to-end stack for run 19, run19-* names only. Test-only; never pointed at the cluster.
# Usage: stack.sh up|down|controller|controller-stop|controller-kill9|token-operator|token-viewer|token-norole|erp CMD...
# WORK (scratch: throwaway SSH key, known_hosts, client secret, user password, logs) is outside every repository and
# never committed. Nothing in this script deletes files: PID files are truncated, the SSH key is created once.
# Ports: pg 39432, kafka 39092, keycloak 39180, erp sftp 39222; order 39081, inventory 39082, adapter 39083, controller 39084.
set -eu
WORK=/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/ef05c591-4bf3-4f8d-9761-3715c9f2aabb/scratchpad/run19-work
BOX=/Users/mike/Documents/ChatGPT/box1
HERE=/Users/mike/Documents/ChatGPT/box1/run19-docs/agent-runs/19-scenario-controller/evidence/scripts
KC=http://localhost:39180/auth
ISS="$KC/realms/box1"
x() { podman exec run19-erp "$@"; }
# ERP domain calls standing in for the operator's console step (local proof only). Arguments travel as environment
# variables, never inside the Python source.
asapp() { podman exec -u box1erp -e BOX1_ERP_CONFIG=/etc/box1-erp/erp.conf -e "A1=${2:-}" -e "A2=${3:-}" run19-erp \
  /usr/lib/box1-erp/venv/bin/python -c \
  "import os; from box1_erp import config, db, domain; c=db.connect(str(config.load().ledger)); A1=os.environ['A1']; A2=os.environ['A2']; $1"; }
ready() { n=0; until curl -sf "$1" >/dev/null 2>&1; do n=$((n+1)); [ $n -gt "${2:-90}" ] && { echo "not ready: $1" >&2; return 1; }; sleep 1; done; }
jvm() {  # name port jar env...
  name=$1; port=$2; jar=$3; shift 3
  env QUARKUS_HTTP_PORT="$port" QUARKUS_LOG_CONSOLE_JSON_ENABLED=true "$@" nohup java -Xmx384m -jar "$jar" >> "$WORK/$name.log" 2>&1 &
  echo $! > "$WORK/$name.pid"; ready "http://localhost:$port/q/health/ready"; echo "$name pid $(cat "$WORK/$name.pid") ready on $port"; }
stopjvm() { if [ -s "$WORK/$1.pid" ]; then kill "$(cat "$WORK/$1.pid")" 2>/dev/null || true; : > "$WORK/$1.pid"; fi; }
secret() { [ -s "$WORK/$1" ] || openssl rand -hex 24 > "$WORK/$1"; cat "$WORK/$1"; }
controller() {
  jvm controller 39084 "$BOX/run19-scenario-controller/target/quarkus-app/quarkus-run.jar" \
    QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://localhost:39432/scenario_controller QUARKUS_DATASOURCE_USERNAME=postgres \
    QUARKUS_DATASOURCE_PASSWORD=postgres SCENARIO_CONTROL_ENABLED=true POD_NAMESPACE=scenario-controller-dev \
    SCENARIO_NAMESPACE_ALLOWLIST=scenario-controller-dev SCENARIO_ENVIRONMENT=local-e2e \
    ORDER_SERVICE_URL=http://localhost:39081 INVENTORY_SERVICE_URL=http://localhost:39082 FULFILLMENT_ADAPTER_URL=http://localhost:39083 \
    INVENTORY_TOKEN_URL="$ISS/protocol/openid-connect/token" INVENTORY_TOKEN_CLIENT_ID=scenario-controller \
    INVENTORY_TOKEN_CLIENT_SECRET="$(cat "$WORK/client-secret")" SCENARIO_JWT_ISSUER="$ISS" \
    SCENARIO_JWKS_URL="$ISS/protocol/openid-connect/certs" SCENARIO_POLL_INTERVAL=PT1S
}
case "$1" in
up)
  mkdir -p "$WORK"
  echo "clocks: host $(date -u +%H:%M:%S) podman-vm $(podman machine ssh date -u +%H:%M:%S | tail -1)"
  podman run -d --name run19-pg -p 127.0.0.1:39432:5432 -e POSTGRES_PASSWORD=postgres --memory 384m docker.io/library/postgres:15-alpine >/dev/null
  podman run -d --name run19-kafka -p 127.0.0.1:39092:9092 --memory 768m \
    -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
    -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:39092 \
    -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT \
    -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
    -e KAFKA_NUM_PARTITIONS=3 docker.io/apache/kafka:4.2.0 >/dev/null
  podman run -d --name run19-keycloak -p 127.0.0.1:39180:8080 --memory 768m -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
    -e "KC_BOOTSTRAP_ADMIN_PASSWORD=$(secret kc-admin)" quay.io/keycloak/keycloak:26.4 start-dev --http-relative-path=/auth >/dev/null
  podman volume create run19-erp-data >/dev/null
  podman run -d --name run19-erp --systemd=always --memory 512m -p 127.0.0.1:39222:22 \
    --mount type=volume,src=run19-erp-data,dst=/srv/box1-erp localhost/run19-erp-harness:dev >/dev/null
  n=0; until podman exec run19-pg pg_isready -q 2>/dev/null; do n=$((n+1)); [ $n -gt 60 ] && exit 1; sleep 1; done; sleep 2
  for db in order_service inventory_service fulfillment scenario_controller; do podman exec run19-pg psql -qU postgres -c "CREATE DATABASE $db"; done
  n=0; until x systemctl is-system-running 2>/dev/null | grep -qE 'running|degraded'; do n=$((n+1)); [ $n -gt 90 ] && exit 1; sleep 1; done
  x /usr/libexec/box1-erp/provision-data-volume.sh --init-ledger >/dev/null
  x sed -i 's/^faults = .*/faults = true/' /etc/box1-erp/erp.conf
  x systemctl reset-failed box1-erp-worker; x systemctl restart box1-erp-worker
  [ -s "$WORK/id_ed25519" ] || ssh-keygen -q -t ed25519 -N '' -C run19-harness-only -f "$WORK/id_ed25519"
  podman cp "$WORK/id_ed25519.pub" run19-erp:/etc/ssh/authorized_keys/erpsftp; x chmod 0644 /etc/ssh/authorized_keys/erpsftp
  printf '[127.0.0.1]:39222 %s\n' "$(x cat /etc/ssh/ssh_host_ed25519_key.pub | cut -d' ' -f1-2)" > "$WORK/known_hosts"
  ready "$KC/realms/master" 120
  sh "$HERE/realm.sh"
  JWKS="$ISS/protocol/openid-connect/certs"
  jvm order 39081 "$BOX/run19-order-service/target/quarkus-app/quarkus-run.jar" \
    QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://localhost:39432/order_service QUARKUS_DATASOURCE_USERNAME=postgres \
    QUARKUS_DATASOURCE_PASSWORD=postgres KAFKA_BOOTSTRAP_SERVERS=localhost:39092 ORDER_OUTBOX_POLL_INTERVAL=200ms
  jvm inventory 39082 "$BOX/run19-inventory-service/target/quarkus-app/quarkus-run.jar" \
    QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://localhost:39432/inventory_service QUARKUS_DATASOURCE_USERNAME=postgres \
    QUARKUS_DATASOURCE_PASSWORD=postgres KAFKA_BOOTSTRAP_SERVERS=localhost:39092 INVENTORY_READ_POLICY=permit \
    INVENTORY_ORDER_EVENTS_FLOOR=2000-01-01T00:00:00Z INVENTORY_JWT_ISSUER="$ISS" INVENTORY_JWKS_URL="$JWKS" INVENTORY_OUTBOX_POLL_INTERVAL=200ms
  jvm adapter 39083 "$BOX/run19-fulfillment-adapter/target/quarkus-app/quarkus-run.jar" \
    QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://localhost:39432/fulfillment QUARKUS_DATASOURCE_USERNAME=postgres \
    QUARKUS_DATASOURCE_PASSWORD=postgres KAFKA_BOOTSTRAP_SERVERS=localhost:39092 FULFILLMENT_READ_POLICY=permit \
    FULFILLMENT_SFTP_ENABLED=true FULFILLMENT_SFTP_HOST=127.0.0.1 FULFILLMENT_SFTP_PORT=39222 \
    FULFILLMENT_SFTP_PRIVATE_KEY_FILE="$WORK/id_ed25519" FULFILLMENT_SFTP_KNOWN_HOSTS_FILE="$WORK/known_hosts" \
    FULFILLMENT_JWT_ISSUER="$ISS" FULFILLMENT_JWKS_URL="$JWKS" FULFILLMENT_OUTBOX_POLL_INTERVAL=200ms \
    FULFILLMENT_RESULTS_POLL_MS=1000
  controller;;
controller) controller;;
controller-stop) stopjvm controller;;
controller-kill9) kill -9 "$(cat "$WORK/controller.pid")"; : > "$WORK/controller.pid";;
down)
  for j in controller adapter inventory order; do stopjvm $j; done
  podman rm -f run19-pg run19-kafka run19-keycloak run19-erp >/dev/null 2>&1 || true
  podman volume rm -f run19-erp-data >/dev/null 2>&1 || true;;
token-operator|token-viewer|token-norole)
  user=${1#token-}
  curl -sf -d grant_type=password -d client_id=scenario-controller -d "client_secret=$(cat "$WORK/client-secret")" \
    -d "username=$user" -d "password=$(cat "$WORK/user-password")" "$ISS/protocol/openid-connect/token" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])';;
erp)  # local stand-in for the operator's console step, through the ERP's own domain API
  shift
  case "$1" in
    mode) asapp "domain.set_mode(c,A1,actor='console',label='run19')" "$2";;
    ship) asapp "print(domain.ship(c,A1,expected_version=None,actor='console',label='run19'))" "$2";;
    hold) asapp "domain.hold(c,A1,expected_version=None,actor='console',label='run19',reason='run19 hold')" "$2";;
    release) asapp "domain.release(c,A1,expected_version=None,actor='console',label='run19')" "$2";;
    fault) asapp "domain.set_fault(c,A1,A2,demo_enabled=True,actor='console',label='run19')" "$2" "$3";;
    ledger) x sqlite3 /srv/box1-erp/state/ledger.db "SELECT request_id,state,shipment_id,version FROM requests ORDER BY request_id";;
    journal) x journalctl -u box1-erp-worker --no-pager -n "${2:-30}";;
    *) echo "unknown erp command" >&2; exit 2;;
  esac;;
*) echo "usage: stack.sh up|down|controller|controller-stop|controller-kill9|token-operator|token-viewer|token-norole|erp ..." >&2; exit 2;;
esac
