#!/bin/sh
# Start or stop the locally built adapter against the run13-* partners. Kills only the PID it started.
# Usage: adapter.sh start|stop|kill9   Env: REPO (adapter clone), WORK (scratch: SFTP key, known_hosts, jwt/pub.pem, logs)
set -eu
REPO=${REPO:?}; WORK=${WORK:?}; PIDF="$WORK/adapter.pid"
case "$1" in
start)
  QUARKUS_HTTP_PORT=${PORT:-28080} \
  QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://localhost:25432/service QUARKUS_DATASOURCE_USERNAME=postgres \
  QUARKUS_DATASOURCE_PASSWORD=postgres KAFKA_BOOTSTRAP_SERVERS=localhost:29092 \
  FULFILLMENT_SFTP_ENABLED=${SFTP:-true} FULFILLMENT_SFTP_HOST=127.0.0.1 FULFILLMENT_SFTP_PORT=22213 \
  FULFILLMENT_SFTP_PRIVATE_KEY_FILE="$WORK/id_ed25519" FULFILLMENT_SFTP_KNOWN_HOSTS_FILE="$WORK/known_hosts" \
  FULFILLMENT_JWT_ISSUER=run13-local FULFILLMENT_JWKS_URL="file:$WORK/jwt/pub.pem" \
  QUARKUS_LOG_CONSOLE_JSON_ENABLED=${JSON:-true} \
  nohup java -jar "$REPO/target/quarkus-app/quarkus-run.jar" >> "$WORK/adapter.log" 2>&1 &
  echo $! > "$PIDF"
  n=0; until curl -sf "localhost:${PORT:-28080}/q/health/ready" >/dev/null; do n=$((n+1)); [ $n -gt 60 ] && { echo "not ready"; exit 1; }; sleep 1; done
  echo "adapter pid $(cat "$PIDF") ready";;
stop) kill "$(cat "$PIDF")" 2>/dev/null || true; sleep 3;;
kill9) kill -9 "$(cat "$PIDF")";;
esac
