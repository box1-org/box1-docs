#!/usr/bin/env python3
"""Local saga with the real order-service and inventory-service jars, real PostgreSQL and Kafka in Podman."""
import json, os, subprocess, sys, time, urllib.request, urllib.error, uuid, signal, datetime
SC = os.path.dirname(os.path.abspath(__file__))
INV = '/Users/mike/Documents/ChatGPT/box1/inventory-service/target/quarkus-app/quarkus-run.jar'
ORD = SC + '/order-e2e/target/quarkus-app/quarkus-run.jar'
PG, KAFKA = 'run12-pg', 'run12-kafka'
PGPORT, KPORT, OPORT, IPORT = 15432, 19092, 18081, 18082
PW = os.environ.get('E2E_DB_PASSWORD', 'throwaway')
procs = {}
def sh(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True).stdout
def http(method, url, body=None, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
def wait(what, fn, limit=150):
    end = time.time() + limit
    while time.time() < end:
        try:
            v = fn()
            if v: return v
        except Exception: pass
        time.sleep(0.5)
    raise SystemExit('TIMEOUT waiting for ' + what)
def app(name, jar, port, env):
    log = open(f'{SC}/e2e-{name}.log', 'a')
    e = dict(os.environ, QUARKUS_HTTP_PORT=str(port), KAFKA_BOOTSTRAP_SERVERS=f'localhost:{KPORT}', QUARKUS_DATASOURCE_PASSWORD=PW,
             QUARKUS_DATASOURCE_JDBC_URL=f'jdbc:postgresql://localhost:{PGPORT}/{name}_service', QUARKUS_DATASOURCE_USERNAME='postgres', **env)
    procs[name] = subprocess.Popen(['java', '-Xmx256m', '-jar', jar], env=e, stdout=log, stderr=log)
    wait(name + ' ready', lambda: http('GET', f'http://localhost:{port}/q/health/ready')[0] == 200)
def stop(name):
    procs[name].send_signal(signal.SIGTERM); procs[name].wait(30)
def order(sku='SKU-42', site='site_nyc', qty=2):
    s, b = http('POST', f'http://localhost:{OPORT}/api/v1/orders', {'customerId': 'cust_e2e_secret', 'sku': sku, 'quantity': qty, 'siteId': site}, {'Content-Type': 'application/json', 'Idempotency-Key': str(uuid.uuid4())})
    assert s == 201, (s, b)
    return json.loads(b)['orderId']
def state(o): return json.loads(http('GET', f'http://localhost:{OPORT}/api/v1/orders/{o}')[1])
def stock(site, sku): return json.loads(http('GET', f'http://localhost:{IPORT}/api/v1/inventory?siteId={site}&sku={sku}')[1])[0]
def sql(db, q): return sh(f'podman exec {PG} psql -U postgres -d {db} -Atc "{q}"').strip()
def topic(t):
    out = sh(f'podman exec {KAFKA} /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:29092 --topic {t} --from-beginning --timeout-ms 4000 2>/dev/null', check=False)
    return [json.loads(l) for l in out.splitlines() if l.startswith('{')]
def check(label, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + label + (' ' + str(detail) if detail else ''), flush=True)
    if not ok: failed.append(label)
failed = []
def main():
    sh(f'podman rm -f {PG} {KAFKA}', check=False)
    sh(f'podman run -d --name {PG} -p {PGPORT}:5432 -e POSTGRES_PASSWORD={PW} docker.io/library/postgres:15-alpine')
    sh(f'podman run -d --name {KAFKA} -p {KPORT}:9092 -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller -e KAFKA_LISTENERS=PLAINTEXT://:9092,INTERNAL://:29092,CONTROLLER://:9093 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:{KPORT},INTERNAL://localhost:29092 -e KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,INTERNAL:PLAINTEXT -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 -e KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 docker.io/apache/kafka:4.2.0')
    wait('postgres', lambda: 'accepting' in sh(f'podman exec {PG} pg_isready', check=False))
    for db in ('order_service', 'inventory_service'):
        sh(f'podman exec {PG} psql -U postgres -c "CREATE DATABASE {db}"')
    wait('kafka', lambda: subprocess.run(f'podman exec {KAFKA} /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --list', shell=True, capture_output=True).returncode == 0)
    for t in ('box1.order.events.v1', 'box1.inventory.events.v1', 'box1.fulfillment.events.v1', 'box1.order.dlq.v1', 'box1.inventory.dlq.v1'):
        sh(f'podman exec {KAFKA} /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --create --topic {t} --partitions 3')
    app('order', ORD, OPORT, {})
    # 1. Retained events, as on the cluster: orders placed before the floor.
    retained = [order(), order()]
    wait('retained events published', lambda: sum(1 for e in topic('box1.order.events.v1') if e['eventType'] == 'order.placed.v1') == 2)
    time.sleep(1.1)
    floor = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    time.sleep(0.2)
    inv_env = {'INVENTORY_ORDER_EVENTS_FLOOR': floor, 'INVENTORY_READ_POLICY': 'permit', 'INVENTORY_METRICS_REFRESH_INTERVAL': '1s'}
    app('inventory', INV, IPORT, inv_env)
    # 2. A new order through the Order API reserves, and Order reaches its expected state.
    live = order()
    wait('order FULFILLMENT_REQUESTED', lambda: state(live)['state'] == 'FULFILLMENT_REQUESTED', 60)
    wait('hold COMMITTED by the signal', lambda: sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{live}'") == 'COMMITTED', 30)
    check('new order reached FULFILLMENT_REQUESTED and its hold COMMITTED', True, live)
    rid = state(live).get('reservationId')
    check('order holds the published reservationId', rid == sql('inventory_service', f"SELECT reservation_id FROM reservations WHERE order_id='{live}'"))
    s = stock('site_nyc', 'SKU-42')
    check('available reflects one hold', s['reserved'] == 2 and s['available'] == 98 and s['onHand'] == 100, s)
    # 3. The retained orders are untouched.
    time.sleep(2)
    check('retained orders stay SUBMITTED', all(state(o)['state'] == 'SUBMITTED' for o in retained))
    check('no reservation for a retained order', sql('inventory_service', "SELECT count(*) FROM reservations WHERE order_id IN ('%s','%s')" % tuple(retained)) == '0')
    m = http('GET', f'http://localhost:{IPORT}/q/metrics')[1]
    skipped = [l for l in m.splitlines() if 'skipped_before_floor' in l and l.startswith('box1_events_consumed_total')]
    check('skip counter counted the 2 retained orders', any(l.split(' ')[1] == '2.0' for l in skipped), skipped)
    # 4. Rejections reach Order.
    for args, code in (((('SKU-NONE'), 'site_nyc', 1), 'UNKNOWN_SKU'), (('SKU-42', 'site_closed', 1), 'SITE_UNAVAILABLE'), (('SKU-LAST', 'site_nyc', 2), 'INSUFFICIENT_STOCK')):
        o = order(*args)
        wait(code, lambda: state(o)['state'] == 'REJECTED', 30)
        reasons = [e for e in topic('box1.inventory.events.v1') if e['aggregateId'] == o]
        check(f'{code} moves Order to REJECTED', len(reasons) == 1 and reasons[0]['payload']['reasonCode'] == code)
    # 5. Final unit over the real path.
    a, b = order('SKU-LAST', 'site_nyc', 1), order('SKU-LAST', 'site_nyc', 1)
    wait('both decided', lambda: {state(a)['state'], state(b)['state']} == {'FULFILLMENT_REQUESTED', 'REJECTED'}, 30)
    check('final unit: one reserved and one rejected', stock('site_nyc', 'SKU-LAST')['available'] == 0 and stock('site_nyc', 'SKU-LAST')['reserved'] == 1)
    # 6. Order never sees customerId from inventory; logs and DB hold none.
    check('no customer ID in inventory events', 'cust_e2e_secret' not in json.dumps(topic('box1.inventory.events.v1')))
    check('no customer ID in the inventory log', 'cust_e2e_secret' not in open(f'{SC}/e2e-inventory.log').read())
    # 7. Expiry reaches Order: stop both, place while inventory is down, order down during the TTL.
    stop('inventory')
    expiring = order('SKU-42', 'site_bos', 1)
    wait('placed published', lambda: any(e['aggregateId'] == expiring for e in topic('box1.order.events.v1')), 30)
    stop('order')
    app('inventory', INV, IPORT, dict(inv_env, INVENTORY_RESERVATION_TTL='PT3S', INVENTORY_EXPIRY_INTERVAL='1s', INVENTORY_EXPIRY_GRACE='PT0S'))
    wait('hold expired with Order down', lambda: sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{expiring}'") == 'EXPIRED', 180)
    app('order', ORD, OPORT, {})
    wait('Order EXCEPTION', lambda: state(expiring)['state'] == 'EXCEPTION', 180)
    check('Order down past the TTL goes to EXCEPTION as ORDER-STATE says', state(expiring)['statusReason'] == 'RESERVATION_EXPIRED', state(expiring)['statusReason'])
    check('expired hold returned stock', stock('site_bos', 'SKU-42')['reserved'] == 0 and stock('site_bos', 'SKU-42')['available'] == 10)
    # 8. A committed hold survives the short TTL and keeps Order healthy.
    stop('inventory')
    app('inventory', INV, IPORT, dict(inv_env, INVENTORY_RESERVATION_TTL='PT10S', INVENTORY_EXPIRY_INTERVAL='1s', INVENTORY_EXPIRY_GRACE='PT0S'))
    healthy = order('SKU-7', 'site_nyc', 1)
    wait('commit', lambda: sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{healthy}'") in ('COMMITTED', 'EXPIRED'), 30)
    time.sleep(12)
    check('a healthy order stays FULFILLMENT_REQUESTED past the TTL', state(healthy)['state'] == 'FULFILLMENT_REQUESTED' and sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{healthy}'") == 'COMMITTED', state(healthy)['state'])
    check('Order dead-letter topic stayed empty', topic('box1.order.dlq.v1') == [])
    check('Inventory dead-letter topic stayed empty', topic('box1.inventory.dlq.v1') == [])
    check('no drift', sql('inventory_service', "SELECT count(*) FROM inventory_stock t WHERE t.reserved <> COALESCE((SELECT sum(r.quantity) FROM reservations r WHERE r.site_id=t.site_id AND r.sku=t.sku AND r.status IN ('ACTIVE','COMMITTED')),0)") == '0')
    # 8a. Runbook replay, with the exact console command: a duplicate has no effect.
    rec = [e for e in topic('box1.order.events.v1') if e['aggregateId'] == live and e['eventType'] == 'order.placed.v1'][0]
    line = live + chr(9) + json.dumps(rec, separators=(',', ':'))
    for _ in range(2):
        subprocess.run(f"podman exec -i {KAFKA} /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:29092 --topic box1.order.events.v1 --property parse.key=true --property \"key.separator=$(printf '\\t')\"", shell=True, input=line + chr(10), text=True, check=True, capture_output=True)
    wait('replay seen', lambda: any('outcome="duplicate"' in l and 'order.placed.v1' in l and l.split(' ')[1] != '0.0' for l in http('GET', f'http://localhost:{IPORT}/q/metrics')[1].splitlines() if l.startswith('box1_events_consumed_total')), 30)
    check('runbook replay of an applied event had no second effect', sql('inventory_service', f"SELECT count(*) FROM reservations WHERE order_id='{live}'") == '1' and sum(1 for e in topic('box1.inventory.events.v1') if e['aggregateId'] == live) == 1)
    # 9. Load sample with production defaults: about 5 orders per second for 60 s, on a large stock row.
    stop('inventory')
    app('inventory', INV, IPORT, inv_env)
    sh(f"podman exec {PG} psql -U postgres -d inventory_service -c \"INSERT INTO inventory_stock (site_id, sku, on_hand, updated_at) VALUES ('site_nyc','SKU-LOAD',100000,now())\"")
    start = time.time(); n = 0; ids = []
    rss_peak = 0
    while time.time() - start < 60:
        ids.append(order('SKU-LOAD', 'site_nyc', 1)); n += 1
        if n % 25 == 0:
            rss_peak = max(rss_peak, int(sh(f"ps -o rss= -p {procs['inventory'].pid}").strip()))
        time.sleep(max(0, n / 5 - (time.time() - start)))
    try:
        wait('all decided', lambda: sql('order_service', "SELECT count(*) FROM orders WHERE sku='SKU-LOAD' AND state='FULFILLMENT_REQUESTED'") == str(n), 120)
    except SystemExit:
        print('DIAG orders by state', sql('order_service', "SELECT state, count(*) FROM orders WHERE sku='SKU-LOAD' GROUP BY state"), flush=True)
        print('DIAG order outbox unpublished', sql('order_service', "SELECT event_type, count(*) FROM outbox WHERE published_at IS NULL GROUP BY event_type"), flush=True)
        print('DIAG inventory holds', sql('inventory_service', "SELECT status, count(*) FROM reservations WHERE sku='SKU-LOAD' GROUP BY status"), flush=True)
        print('DIAG inventory outbox unpublished', sql('inventory_service', "SELECT count(*) FROM outbox WHERE published_at IS NULL"), flush=True)
        print('DIAG groups', sh(f'podman exec {KAFKA} /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:29092 --describe --all-groups', check=False), flush=True)
        failed.append('load')
    m = http('GET', f'http://localhost:{IPORT}/q/metrics')[1]
    age = [l for l in m.splitlines() if l.startswith('box1_event_age_seconds_max') or l.startswith('box1_outbox_publish_lag_seconds_max')]
    print(f'LOAD orders={n} seconds={time.time()-start:.0f} inventory_rss_peak_mib={rss_peak//1024} {age}', flush=True)
    check('load: one reservation per order, none lost', sql('inventory_service', "SELECT reserved FROM inventory_stock WHERE sku='SKU-LOAD'") == str(n))
    # 8b. Database restart: readiness falls and returns, without restarting either application.
    sh(f'podman stop {PG}')
    wait('inventory unready', lambda: http('GET', f'http://localhost:{IPORT}/q/health/ready')[0] == 503, 60)
    check('inventory live while the database is down', http('GET', f'http://localhost:{IPORT}/q/health/live')[0] == 200)
    down_order_probe = http('GET', f'http://localhost:{IPORT}/api/v1/inventory')[0]
    check('reads answer 503 while the database is down', down_order_probe == 503, down_order_probe)
    t0 = time.time(); sh(f'podman start {PG}')
    wait('inventory ready again', lambda: http('GET', f'http://localhost:{IPORT}/q/health/ready')[0] == 200, 120)
    print(f'DB_RECOVERY ready after {time.time()-t0:.1f}s', flush=True)
    wait('order ready again', lambda: http('GET', f'http://localhost:{OPORT}/q/health/ready')[0] == 200, 120)
    # 8c. The gate: Inventory restarts with a TTL shorter than its grace. The signal still wins, and Order stays healthy.
    stop('inventory')
    gated = order('SKU-7', 'site_nyc', 1)
    wait('placed published', lambda: any(e['aggregateId'] == gated for e in topic('box1.order.events.v1')), 30)
    app('inventory', INV, IPORT, dict(inv_env, INVENTORY_RESERVATION_TTL='PT2S', INVENTORY_EXPIRY_INTERVAL='1s', INVENTORY_EXPIRY_GRACE='PT40S'))
    wait('commit under the gate', lambda: sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{gated}'") in ('COMMITTED', 'EXPIRED'), 60)
    time.sleep(3)
    check('after a restart the unread signal beats a short TTL', sql('inventory_service', f"SELECT status FROM reservations WHERE order_id='{gated}'") == 'COMMITTED' and state(gated)['state'] == 'FULFILLMENT_REQUESTED')
    print('RESULT', 'FAILED ' + str(failed) if failed else 'ALL PASS', flush=True)
try:
    main()
finally:
    for p in procs.values():
        p.kill()
    sh(f'podman rm -f {PG} {KAFKA}', check=False)
