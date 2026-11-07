#!/usr/bin/env python3
"""Phase 4 scenarios for box1-docs#13 against the real #14 ERP harness (run13-erp), run13-pg and run13-kafka.

Drives the locally built adapter through adapter.sh with shortened D-004 timers. Prints one PASS/FAIL line per check.
Usage: WORK=<scratch> REPO=<adapter clone> python3 -I scenarios.py [scenario ...]
Only run13-* containers and the adapter PID this script started are touched.
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ['WORK']
BASE = 'http://localhost:28080'
RUN = time.strftime('%H%M%S')
RESULTS = []
ENV = dict(os.environ, FULFILLMENT_ACK_TIMEOUT_BASE_SECONDS='5', FULFILLMENT_ACK_TIMEOUT_MAX_SECONDS='10',
           FULFILLMENT_ACK_MAX_UPLOADS='3', FULFILLMENT_PROBE_INTERVAL_SECONDS='15',
           FULFILLMENT_UPLOAD_BACKOFF_BASE_SECONDS='2', FULFILLMENT_UPLOAD_BACKOFF_MAX_SECONDS='4',
           FULFILLMENT_UPLOAD_MAX_ATTEMPTS='5', FULFILLMENT_DISPATCH_LEASE_SECONDS='10', FULFILLMENT_RECONCILE_POLL_MS='1000',
           FULFILLMENT_METRICS_REFRESH_INTERVAL='1s', FULFILLMENT_HIDDEN_SWEEP_MS='5000')


def sh(*args, check=False, env=None):
    p = subprocess.run(args, capture_output=True, text=True, env=env or ENV)
    if check and p.returncode != 0:
        raise RuntimeError(f'{args[0]} failed: {p.stderr.strip()[:300]}')
    return p.stdout.strip()


def erp(*args):
    return sh(os.path.join(HERE, 'erp-harness.sh'), *args, check=True)


def adapter(cmd, **extra):
    env = dict(ENV, **extra)
    return sh(os.path.join(HERE, 'adapter.sh'), cmd, env=env)


SAFE = __import__('re').compile(r'^[A-Za-z0-9_.%-]+$')


def psql(sql, *values):
    """Test-only helper. Values interpolated into SQL are IDs from ids(), which validates them."""
    for v in values:
        assert SAFE.match(v), 'unsafe value'
    sql = sql.format(*values) if values else sql
    return sh('podman', 'exec', 'run13-pg', 'psql', '-U', 'postgres', '-d', 'service', '-At', '-F', '|', '-c', sql)


def token(role='fulfillment-writer'):
    return sh('node', os.path.join(HERE, 'mint-token.mjs'), os.path.join(WORK, 'jwt', 'key.pem'), role, check=True)


def http(method, path, body=None, auth=True, headers=None):
    req = urllib.request.Request(BASE + path, method=method, data=None if body is None else json.dumps(body).encode())
    req.add_header('Content-Type', 'application/json')
    if auth:
        req.add_header('Authorization', 'Bearer ' + token())
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        return 0, {}, str(e)


def status(fid):
    code, _, body = http('GET', f'/api/fulfillments/{fid}')
    return json.loads(body) if code == 200 else {'http': code}


def wait(desc, predicate, timeout=60):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            last = predicate()
            if last:
                return last
        except Exception as e:  # noqa: BLE001 - keep polling through transient errors
            last = repr(e)
        time.sleep(1)
    return None


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}", flush=True)


def ids(tag):
    n = f'{tag}{RUN}'
    assert SAFE.match(n), 'unsafe id'  # every ID interpolated into SQL or shell comes from here
    return f'ful_{n}', f'ord_{n}', {'fulfillmentRequestId': f'ful_{n}', 'orderId': f'ord_{n}', 'reservationId': f'res_{n}',
                                    'siteId': 'site_lab', 'sku': 'PUMP-1', 'quantity': 1}


def events(fid):
    out = sh('podman', 'exec', 'run13-kafka', '/opt/kafka/bin/kafka-console-consumer.sh', '--bootstrap-server',
             'localhost:9092', '--topic', 'box1.fulfillment.events.v1', '--from-beginning', '--timeout-ms', '4000')
    return [json.loads(l) for l in out.splitlines() if l.startswith('{') and fid in l]


def uploads(fid):
    return psql(f"SELECT reason, state FROM upload WHERE fulfillment_request_id = '{fid}' ORDER BY started_at").splitlines()


def erp_state(fid):
    return sh('podman', 'exec', 'run13-erp', 'sqlite3', '/srv/box1-erp/state/ledger.db',
              f"SELECT state, shipment_id, version FROM requests WHERE request_id = '{fid}'")


def outcome(fid, value):
    return lambda: status(fid).get('outcome') == value


# ---------------------------------------------------------------- scenarios

def s_held_released_shipped():
    fid, oid, body = ids('hrs')
    code, h, _ = http('POST', '/api/fulfillments', body, headers={'X-Correlation-ID': f'corr-{fid}'})
    check('held: REST accepted 202 with Location', code == 202 and h.get('Location') == f'/api/fulfillments/{fid}')
    check('held: ERP acknowledged revision 1 PENDING', wait('', outcome(fid, 'PENDING'), 30))
    erp('hold', fid)
    check('held: HELD applied (revision 2)', wait('', outcome(fid, 'HELD'), 30))
    time.sleep(20)  # longer than the 5 s ack timeout and the 15 s probe interval
    s = status(fid)
    check('held: waiting is not a transport failure', s['outcome'] == 'HELD' and s['dispatch'] == 'UPLOADED'
          and s['needsAttentionReason'] is None, f"dispatch={s['dispatch']} resends={s['resends']}")
    probes = [u for u in uploads(fid) if u.startswith('PROBE')]
    dup = psql(f"SELECT count(*) FROM erp_file_receipt WHERE fulfillment_request_id = '{fid}' AND outcome = 'DUPLICATE'")
    check('held: slow probe is an equivalent resend the ERP answers by republishing (duplicate)',
          len(probes) >= 1 and int(dup) >= 1, f'probes={len(probes)} duplicate receipts={dup}')
    erp('release', fid)
    check('held: released back to PENDING (revision 3)', wait('', lambda: status(fid).get('revision') == 3, 30))
    shp = erp('ship', fid)
    check('held: manual ship applied as SHIPPED (revision 4)', wait('', outcome(fid, 'SHIPPED'), 30))
    ev = wait('', lambda: events(fid), 30) or []
    check('held: exactly one shipment.confirmed.v1 with the ERP shipmentId', len(ev) == 1
          and ev[0]['eventType'] == 'shipment.confirmed.v1' and ev[0]['payload']['shipmentId'] == shp
          and ev[0]['correlationId'] == f'corr-{fid}', shp)
    check('held: ERP ledger agrees', erp_state(fid).startswith(f'SHIPPED|{shp}'))
    return fid


def s_rejected():
    fid, oid, body = ids('rej')
    http('POST', '/api/fulfillments', body)
    wait('', outcome(fid, 'PENDING'), 30)
    erp('reject', fid, 'STOCK_UNAVAILABLE')
    check('reject: REJECTED applied', wait('', outcome(fid, 'REJECTED'), 30))
    ev = wait('', lambda: events(fid), 30) or []
    text = json.dumps(ev)
    check('reject: shipment.failed.v1 retryable:false with reasonCode, no reason text', len(ev) == 1
          and ev[0]['payload'] == {'orderId': oid, 'fulfillmentRequestId': fid, 'retryable': False,
                                   'reasonCode': 'STOCK_UNAVAILABLE'} and 'do not copy' not in text)
    check('reject: status API shows code, no text', status(fid).get('reasonCode') == 'STOCK_UNAVAILABLE'
          and 'do not copy' not in json.dumps(status(fid)))


def s_auto_and_kafka():
    erp('mode', 'AUTO')
    try:
        fid, oid, body = ids('kaf')
        ev = {'eventId': str(uuid.uuid4()), 'eventType': 'fulfillment.requested.v1', 'schemaVersion': 1, 'aggregateId': oid,
              'occurredAt': '2026-11-06T00:30:00.123456Z', 'correlationId': f'corr-{fid}',
              'causationId': str(uuid.uuid4()), 'traceparent': '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
              'payload': {k: body[k] for k in ('orderId', 'reservationId', 'fulfillmentRequestId', 'siteId', 'sku', 'quantity')}}
        line = oid + '|' + json.dumps(ev)
        for _ in range(2):  # Kafka redelivery of the same event
            subprocess.run(['podman', 'exec', '-i', 'run13-kafka', '/opt/kafka/bin/kafka-console-producer.sh',
                            '--bootstrap-server', 'localhost:9092', '--topic', 'box1.order.events.v1', '--property',
                            'parse.key=true', '--property', 'key.separator=|'], input=line + '\n', text=True,
                           capture_output=True)
        code, _, _ = http('POST', '/api/fulfillments', body)  # REST for the same request
        check('kafka: AUTO ship from a Kafka event', wait('', outcome(fid, 'SHIPPED'), 40))
        s = status(fid)
        check('kafka: one request, origin EVENT, REST repeat equivalent', s['origin'] == 'EVENT' and code in (200, 202),
              f'rest={code}')
        rows = sh('podman', 'exec', 'run13-erp', 'sqlite3', '/srv/box1-erp/state/ledger.db',
                  f"SELECT count(*) FROM shipments WHERE request_id = '{fid}'")
        check('kafka: ERP holds exactly one shipment', rows == '1', rows)
        ev2 = wait('', lambda: events(fid), 30) or []
        check('kafka: one confirmed event; trace carried through ERP1',
              len(ev2) == 1 and ev2[0]['traceparent'] == ev['traceparent'] and ev2[0]['causationId'] == ev['eventId'])
    finally:
        erp('mode', 'MANUAL')


def s_sftp_down_then_recovered():
    fid, oid, body = ids('sfd')
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'stop', 'sshd')
    code, _, _ = http('POST', '/api/fulfillments', body)
    check('sftp-down: accepted durably while SFTP is down', code == 202)
    failed = wait('', lambda: psql(f"SELECT count(*) FROM upload WHERE fulfillment_request_id='{fid}' AND state='FAILED'")
                  >= '2', 30)
    s = status(fid)
    check('sftp-down: bounded retries recorded, not a business outcome', failed and s['outcome'] == 'AWAITING_ERP'
          and s['failedUploadAttempts'] >= 2 and s['lastError'] in ('CONNECTION_REFUSED', 'CONNECTION_CLOSED'), f"attempts={s['failedUploadAttempts']} lastError={s['lastError']}")
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'start', 'sshd')
    check('sftp-down: recovered and acknowledged after SFTP returns', wait('', outcome(fid, 'PENDING'), 40))


def s_host_key():
    fid, oid, body = ids('hk')
    erp('rekey')
    http('POST', '/api/fulfillments', body)
    wait('', lambda: psql(f"SELECT count(*) FROM upload WHERE fulfillment_request_id='{fid}' AND state='FAILED'") >= '1', 30)
    s = status(fid)
    inbound = sh('podman', 'exec', 'run13-erp', 'sh', '-c', 'ls -a /srv/box1-erp/exchange/inbound')
    check('host-key: changed host key refuses the connection; nothing uploaded', s['uploads'] == 0
          and s['failedUploadAttempts'] >= 1 and s['lastError'] == 'HOST_KEY_REJECTED' and fid not in inbound, f"lastError={s['lastError']}")
    open(os.path.join(WORK, 'known_hosts'), 'w').close()  # unknown host: empty known_hosts
    before = s['failedUploadAttempts']
    wait('', lambda: status(fid)['failedUploadAttempts'] > before, 20)
    s = status(fid)
    check('host-key: unknown host key also refused (no accept-new)', s['uploads'] == 0
          and s['lastError'] == 'HOST_KEY_REJECTED', f"lastError={s['lastError']}")
    erp('trust')  # operator installs the new key out of band
    check('host-key: uploads resume once the new key is trusted', wait('', outcome(fid, 'PENDING'), 40))


def s_lost_upload():
    fid, oid, body = ids('lup')
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'stop', 'box1-erp-worker')
    http('POST', '/api/fulfillments', body)
    wait('', lambda: status(fid).get('uploads', 0) >= 1, 30)
    sh('podman', 'exec', 'run13-erp', 'sh', '-c', f'rm -f /srv/box1-erp/exchange/inbound/REQ.{fid}.*')  # the upload is lost
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'start', 'box1-erp-worker')
    check('lost-upload: ack timeout leads to an equivalent resend that the ERP acknowledges',
          wait('', outcome(fid, 'PENDING'), 60))
    u = uploads(fid)
    nonces = psql(f"SELECT count(DISTINCT nonce) FROM upload WHERE fulfillment_request_id='{fid}'")
    check('lost-upload: resend used a new nonce', any(x.startswith('NO_ACK') for x in u) and int(nonces) >= 2, str(u))


def s_lost_result():
    fid, oid, body = ids('lre')
    http('POST', '/api/fulfillments', body)
    wait('', outcome(fid, 'PENDING'), 30)
    adapter('stop')
    shp = erp('ship', fid)
    time.sleep(3)
    sh('podman', 'exec', 'run13-erp', 'sh', '-c', f'rm -f /srv/box1-erp/exchange/outbound/RES.{fid}.*')  # result lost
    adapter('start')
    check('lost-result: slow probe recovers the lost SHIPPED result', wait('', outcome(fid, 'SHIPPED'), 60))
    check('lost-result: shipment matches the ERP', status(fid)['shipmentId'] == shp)


def s_crash_before_upload_and_restart():
    adapter('stop')
    adapter('start', FULFILLMENT_SFTP_ENABLED='false')
    a, _, body_a = ids('cra')
    b, _, body_b = ids('crb')
    ca, _, _ = http('POST', '/api/fulfillments', body_a)
    cb, _, _ = http('POST', '/api/fulfillments', body_b)
    check('crash: both accepted (202) with SFTP unavailable', ca == 202 and cb == 202)
    adapter('kill9')
    time.sleep(2)
    adapter('start')
    check('crash: accepted work survives kill -9 and is dispatched after restart',
          wait('', lambda: outcome(a, 'PENDING')() and outcome(b, 'PENDING')(), 60))


def s_interrupted_upload():
    fid, oid, body = ids('int')
    sh('podman', 'pause', 'run13-erp')  # a hung transfer
    http('POST', '/api/fulfillments', body)
    started = wait('', lambda: psql(f"SELECT state FROM upload WHERE fulfillment_request_id='{fid}'") == 'STARTED', 30)
    adapter('kill9')
    sh('podman', 'unpause', 'run13-erp')
    adapter('start')
    check('interrupted: an upload in flight at a crash is retried under a new nonce after the lease',
          started and wait('', outcome(fid, 'PENDING'), 60), str(uploads(fid)))
    tmp = sh('podman', 'exec', 'run13-erp', 'sh', '-c', 'ls -a /srv/box1-erp/exchange/inbound')
    check('interrupted: ERP never imported a partial file', erp_state(fid).count('|') == 2, tmp.replace('\n', ' '))


def s_needs_attention_and_operator():
    adapter('stop')
    adapter('start', FULFILLMENT_ACK_MAX_UPLOADS='2')
    fid, oid, body = ids('nat')
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'stop', 'box1-erp-worker')
    http('POST', '/api/fulfillments', body)
    na = wait('', lambda: status(fid).get('dispatch') == 'NEEDS_ATTENTION', 60)
    s = status(fid)
    check('exhaustion: no acknowledgement after the bound moves to needs-attention, not a failure', na
          and s['needsAttentionReason'] == 'NO_ACKNOWLEDGEMENT' and s['outcome'] == 'AWAITING_ERP' and not events(fid))
    check('exhaustion: anonymous operator call refused',
          http('POST', f'/internal/fulfillments/{fid}/reconcile', auth=False)[0] == 401)
    code, _, _ = http('POST', f'/internal/fulfillments/{fid}/reconcile')
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'start', 'box1-erp-worker')
    check('exhaustion: operator reconcile requeues; late acknowledgement applies', code == 202
          and wait('', outcome(fid, 'PENDING'), 60))
    audit = psql(f"SELECT action, actor FROM audit WHERE fulfillment_request_id='{fid}'")
    check('exhaustion: reconcile audited with the token subject', 'RECONCILE_REQUEUED|run13-operator' in audit, audit)
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'stop', 'sshd')
    f2, _, b2 = ids('nau')
    http('POST', '/api/fulfillments', b2)
    check('exhaustion: upload failures stop at the bound with UPLOAD_EXHAUSTED',
          wait('', lambda: status(f2).get('needsAttentionReason') == 'UPLOAD_EXHAUSTED', 90))
    sh('podman', 'exec', 'run13-erp', 'systemctl', 'start', 'sshd')
    code, _, resp = http('POST', '/internal/fulfillments/reconcile?reason=UPLOAD_EXHAUSTED&limit=50')
    check('exhaustion: bulk reconcile after the outage requeues and the request is acknowledged',
          code == 202 and f2 in resp and wait('', outcome(f2, 'PENDING'), 60), resp[:120])
    check('exhaustion: bulk reconcile refuses CONFLICTING_REUSE',
          http('POST', '/internal/fulfillments/reconcile?reason=CONFLICTING_REUSE')[0] == 400)
    adapter('stop')
    adapter('start')


def s_redelivery_and_reemit(fid):
    before = len(events(fid))
    erp('reemit', fid)
    time.sleep(6)
    name = sh('podman', 'exec', 'run13-erp', 'sh', '-c',
              f'ls /srv/box1-erp/exchange/consumed | grep "^RES.{fid}.000004" | head -1')
    sh('podman', 'exec', 'run13-erp', 'sh', '-c',
       f'cp -p /srv/box1-erp/exchange/consumed/{name} /srv/box1-erp/exchange/outbound/.x.tmp && '
       f'mv /srv/box1-erp/exchange/outbound/.x.tmp /srv/box1-erp/exchange/outbound/{name.rsplit(".", 1)[0]}')
    time.sleep(6)
    dup = psql(f"SELECT count(*) FROM erp_file_receipt WHERE fulfillment_request_id='{fid}' AND outcome='DUPLICATE'")
    applied = psql(f"SELECT count(*) FROM erp_result WHERE fulfillment_request_id='{fid}' AND revision=4")
    check('redelivery: re-emitted and redelivered SHIPPED results are duplicates; no new event',
          int(dup) >= 1 and applied == '1' and len(events(fid)) == before == 1, f'duplicate receipts={dup}')


def s_conflicting_reuse():
    fid, oid, body = ids('cfl')
    other = (f'HDR|ERP1|REQ|2026-11-06T00:00:00.000Z\nREQ|{fid}|{oid}|res_other|site_lab|API|2026-11-06T00:00:00.000Z||\n'
             'LIN|1|PUMP-9|9\nTRL|4\n')
    path = os.path.join(WORK, 'other.erp1')
    open(path, 'w').write(other)
    batch = os.path.join(WORK, 'batch')
    open(batch, 'w').write(f'put {path} inbound/.REQ.{fid}.ffffffff.erp1.tmp\n'
                           f'rename inbound/.REQ.{fid}.ffffffff.erp1.tmp inbound/REQ.{fid}.ffffffff.erp1\n')
    sh('sftp', '-i', os.path.join(WORK, 'id_ed25519'), '-o', 'IdentitiesOnly=yes', '-o',
       'UserKnownHostsFile=' + os.path.join(WORK, 'known_hosts'), '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes',
       '-P', '22213', '-b', batch, 'erpsftp@127.0.0.1', check=True)
    time.sleep(4)
    http('POST', '/api/fulfillments', body)
    check('conflict: real ERP CONFLICTING_REUSE moves the request to needs-attention',
          wait('', lambda: status(fid).get('needsAttentionReason') == 'CONFLICTING_REUSE', 40))
    s = status(fid)
    q = psql(f"SELECT reason FROM erp_file_receipt WHERE fulfillment_request_id IS NULL AND file_name LIKE 'RES.{fid}.%'")
    check('conflict: the other writer\'s earlier result was quarantined as UNKNOWN_REQUEST; no resend after the ERR',
          s['dispatch'] == 'NEEDS_ATTENTION' and s['uploads'] == 1 and 'UNKNOWN_REQUEST' in q, f"outcome={s['outcome']} q={q}")


def s_hidden_name():
    sh('podman', 'exec', 'run13-erp', 'sh', '-c',
       f'echo hi > /srv/box1-erp/exchange/outbound/.hidden-{RUN} && chgrp erpxfer /srv/box1-erp/exchange/outbound/.hidden-{RUN} && chmod 660 /srv/box1-erp/exchange/outbound/.hidden-{RUN}')
    moved = wait('', lambda: f'_hidden-{RUN}.' in sh('podman', 'exec', 'run13-erp', 'ls', '/srv/box1-erp/exchange/consumed'), 20)
    check('unexpected: a hidden non-.tmp name is quarantined and moved too', moved)


def s_unexpected_name():
    sh('podman', 'exec', 'run13-erp', 'sh', '-c',
       f'echo hello > /srv/box1-erp/exchange/outbound/notes-{RUN}.txt && chgrp erpxfer /srv/box1-erp/exchange/outbound/notes-{RUN}.txt && chmod 660 /srv/box1-erp/exchange/outbound/notes-{RUN}.txt')
    moved = wait('', lambda: f'notes-{RUN}.txt.' in sh('podman', 'exec', 'run13-erp', 'ls', '/srv/box1-erp/exchange/consumed'), 20)
    q = psql(f"SELECT reason FROM erp_file_receipt WHERE file_name = 'notes-{RUN}.txt'")
    check('unexpected: quarantined on the adapter side and moved to consumed/', moved and q == 'UNEXPECTED_NAME', q)


def s_storage_down():
    fid, oid, body = ids('sto')
    sh('podman', 'stop', 'run13-pg')
    code, _, resp = http('POST', '/api/fulfillments', body)
    ready = urllib.request.urlopen
    try:
        rc = ready(BASE + '/q/health/ready', timeout=10).status
    except urllib.error.HTTPError as e:
        rc = e.code
    check('storage: acceptance refused with 503 while PostgreSQL is down', code == 503, f'post={code} body={resp[:120]}')
    check('storage: readiness reports DOWN', rc == 503)
    tok = token()
    req = urllib.request.Request(BASE + f'/internal/fulfillments/{fid}/reconcile', method='POST', data=b'')
    req.add_header('Authorization', 'Bearer ' + tok)
    req.add_header('X-Probe-Header', 'echo-check')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            rcode, rheaders, rbody = r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        rcode, rheaders, rbody = e.code, dict(e.headers), e.read().decode()
    leaked = any(tok in v or 'echo-check' in v for v in rheaders.values()) or tok in rbody or 'at org.' in rbody
    check('storage: operator call during the outage is a problem document with no echoed headers or stack trace',
          rcode == 503 and 'problem' in rheaders.get('Content-Type', '') and not leaked, f'{rcode} {rbody[:80]}')
    sh('podman', 'start', 'run13-pg')
    time.sleep(5)
    check('storage: nothing was accepted while down', psql(f"SELECT count(*) FROM fulfillment_request WHERE fulfillment_request_id='{fid}'") == '0')
    code2, _, _ = http('POST', '/api/fulfillments', body)
    check('storage: accepted after recovery', code2 == 202)


def s_logs_and_metrics(fid):
    lines = [json.loads(l) for l in open(os.path.join(WORK, 'adapter.log')) if l.startswith('{') and fid in l]
    msgs = [l['message'] for l in lines]
    check('logs: request, upload, ERP result and outcome event correlate by fulfillmentRequestId',
          any('accepted' in m or 'created' in m for m in msgs) and any('Uploaded' in m for m in msgs)
          and any('Applied ERP result' in m and 'outcomeEvent=' in m and 'none' not in m for m in msgs),
          f'{len(lines)} lines')
    check('logs: no SKU, quantity or reason text in any log line',
          not any('PUMP-1' in json.dumps(l) or 'do not copy' in json.dumps(l) for l in
                  (json.loads(x) for x in open(os.path.join(WORK, 'adapter.log')) if x.startswith('{'))))
    m = urllib.request.urlopen(BASE + '/q/metrics', timeout=10).read().decode()
    names = ['fulfillment_backlog', 'fulfillment_oldest_unacknowledged_seconds', 'fulfillment_resends_total',
             'fulfillment_quarantined_files', 'fulfillment_needs_attention', 'fulfillment_uploads_total',
             'fulfillment_held', 'fulfillment_erp_errors_total']
    check('metrics: backlog, oldest pending age, retries/resends, quarantined, needs-attention exposed',
          all(n in m for n in names), ' '.join(n for n in names if n not in m))
    print('\n'.join(l for l in m.splitlines() if l.startswith('fulfillment_')))


SCENARIOS = ['held', 'reject', 'kafka', 'sftp', 'hostkey', 'lostupload', 'lostresult', 'crash', 'interrupted',
             'attention', 'conflict', 'unexpected', 'storage', 'logs']

if __name__ == '__main__':
    chosen = sys.argv[1:] or SCENARIOS
    print(f"clocks: host {time.strftime('%H:%M:%S', time.gmtime())} podman-vm "
          f"{sh('podman', 'machine', 'ssh', 'date', '-u', '+%H:%M:%S')}  run={RUN}")
    adapter('stop')
    adapter('start')
    shipped = None
    for s in chosen:
        print(f'== {s}', flush=True)
        if s == 'held':
            shipped = s_held_released_shipped()
        elif s == 'reject':
            s_rejected()
        elif s == 'kafka':
            s_auto_and_kafka()
        elif s == 'sftp':
            s_sftp_down_then_recovered()
        elif s == 'hostkey':
            s_host_key()
        elif s == 'lostupload':
            s_lost_upload()
        elif s == 'lostresult':
            s_lost_result()
        elif s == 'crash':
            s_crash_before_upload_and_restart()
        elif s == 'interrupted':
            s_interrupted_upload()
        elif s == 'attention':
            s_needs_attention_and_operator()
        elif s == 'conflict':
            s_conflicting_reuse()
        elif s == 'unexpected':
            s_unexpected_name()
            s_hidden_name()
        elif s == 'storage':
            s_storage_down()
        elif s == 'logs':
            if shipped:
                s_redelivery_and_reemit(shipped)
                s_logs_and_metrics(shipped)
    print(f"clocks after: host {time.strftime('%H:%M:%S', time.gmtime())} podman-vm "
          f"{sh('podman', 'machine', 'ssh', 'date', '-u', '+%H:%M:%S')}")
    passed = sum(1 for _, ok in RESULTS if ok)
    print(f'== {passed}/{len(RESULTS)} checks passed')
    sys.exit(0 if passed == len(RESULTS) else 1)
