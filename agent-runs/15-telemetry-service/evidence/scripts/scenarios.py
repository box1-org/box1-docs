"""Phase 4 verification scenarios for box1-docs#15, run against the packaged jar and local run15-* containers.
Usage: python3 -I scenarios.py <scenario> [...]. Prints a redacted evidence log on stdout. No credential is printed."""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console_client import Console  # noqa: E402

SCRATCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'http://localhost:18080'
CREDS = json.load(open(os.path.join(SCRATCH, 'keycloak', 'local-test-users.json')))
PIDFILE = os.path.join(SCRATCH, 'app.pid')
LOAD = {'kind': 'LOAD', 'sites': 2, 'assetsPerSite': 2, 'metrics': ['vibration'], 'ratePerAsset': 5, 'durationSeconds': 12}


def log(*parts):
    print(datetime.now(timezone.utc).strftime('%H:%M:%SZ'), *parts, flush=True)


def check(label, ok, detail=''):
    log('PASS' if ok else 'FAIL', label, detail)
    if not ok:
        check.failures += 1


check.failures = 0


def sql(query):
    return subprocess.check_output(['podman', 'exec', 'run15-pg', 'psql', '-U', 'asset_service', '-d', 'asset_service', '-tAc', query],
                                   text=True).strip()


def app_stop(hard=False):
    if not os.path.exists(PIDFILE):
        return
    pid = int(open(PIDFILE).read().strip())
    try:
        os.kill(pid, signal.SIGKILL if hard else signal.SIGTERM)
    except ProcessLookupError:
        pass
    for _ in range(40):
        try:
            os.kill(pid, 0)
            time.sleep(0.25)
        except ProcessLookupError:
            break
    os.remove(PIDFILE)


def app_start(**env):
    environment = dict(os.environ, **env)
    out = open(os.path.join(SCRATCH, 'app.log'), 'a')
    process = subprocess.Popen([os.path.join(SCRATCH, 'run-local.sh')], env=environment, stdout=out, stderr=subprocess.STDOUT,
                               start_new_session=True)
    open(PIDFILE, 'w').write(str(process.pid))
    for _ in range(60):
        try:
            with urllib.request.urlopen(BASE + '/q/health/ready', timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('app did not become ready')


def operator():
    console = Console(BASE)
    console.login('operator', CREDS['operator'])
    return console


def start_run(console, body):
    status, armed = console.call('/api/v1/control/runs', 'POST', body)
    assert status == 201, (status, armed)
    status, started = console.call('/api/v1/control/runs/%s/start' % armed['runId'], 'POST',
                                   {'confirmToken': armed['confirmToken'], 'confirmNamespace': armed['namespace']})
    assert status == 200, (status, started)
    return armed


def run(console, run_id):
    return console.call('/api/v1/control/runs/' + run_id)[1]


def wait(label, condition, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        value = condition()
        if value:
            return value
        time.sleep(0.5)
    raise AssertionError('timed out: ' + label)


def metric(name, **labels):
    text = urllib.request.urlopen(BASE + '/q/metrics', timeout=5).read().decode()
    total = 0.0
    for line in text.splitlines():
        metric_name = line.split('{', 1)[0].split(' ', 1)[0]
        if metric_name == name and all('%s="%s"' % (k, v) in line for k, v in labels.items()):
            total += float(line.split(' # ', 1)[0].rsplit(' ', 1)[1])  # drop any OpenMetrics exemplar suffix
    return total


def find_seed(console, entry, body, limit=400, accept=lambda marker: True):
    """A seed whose first chaos injection is `entry`, found with the preview endpoint (publishes nothing)."""
    for n in range(1, limit):
        seed = '%016x' % (0x5eed000000000000 + n)
        status, preview = console.call('/api/v1/control/preview?limit=200', 'POST', dict(body, seed=seed))
        markers = [l for l in preview['lines'] if '|I|' in l]
        if markers and markers[0].split('|I|')[1].startswith(entry + ' ') and accept(markers[0].split('|I|')[1]):
            return seed, markers[0]
    raise AssertionError('no seed found for ' + entry)


def s_access():
    anonymous = Console(BASE)
    page = anonymous._open(urllib.request.Request(BASE + '/console/'))
    check('anonymous console page redirects to Keycloak', page.status == 302 and '/auth/realms/box1/' in page.headers['Location'],
          str(page.status))
    check('anonymous control state (JS) is refused', anonymous.call('/api/v1/control/state')[0] == 499)
    stop = anonymous.call('/api/v1/control/stop-all', 'POST')[0]
    check('anonymous stop-all is refused', stop in (302, 401, 499), str(stop))
    for method, path in [('POST', '/api/v1/telemetry/readings'), ('GET', '/api/v1/alerts'), ('GET', '/api/v1/assets/asset_x/readings')]:
        request = urllib.request.Request(BASE + path, method=method, data=b'{}' if method == 'POST' else None,
                                         headers={'Content-Type': 'application/json'})
        status = anonymous._open(request).status
        check('anonymous %s %s is 401' % (method, path), status == 401, str(status))
    viewer = Console(BASE)
    viewer.login('viewer', CREDS['viewer'])
    check('no-role user: console page 403', viewer._open(urllib.request.Request(BASE + '/console/')).status == 403)
    check('no-role user: state 403', viewer.call('/api/v1/control/state')[0] == 403)
    check('no-role user: arm 403', viewer.call('/api/v1/control/runs', 'POST', LOAD)[0] == 403)
    check('no-role user: stop-all 403', viewer.call('/api/v1/control/stop-all', 'POST')[0] == 403)
    op = operator()
    status, state = op.call('/api/v1/control/state')
    check('operator: state 200 with actor from token', status == 200 and state['actor'] == 'operator', state.get('actor'))
    check('operator: page served from this pod', op._open(urllib.request.Request(BASE + '/console/')).status == 200)


def s_caps():
    op = operator()
    cases = [({'kind': 'LOAD', 'sites': 6}, 'LIMIT_EXCEEDED'),
             ({'kind': 'LOAD', 'sites': 5, 'assetsPerSite': 11, 'metrics': ['power'], 'ratePerAsset': 1}, 'RATE_CAP'),
             ({'kind': 'LOAD', 'durationSeconds': 901}, 'LIMIT_EXCEEDED'),
             ({'kind': 'LOAD', 'ratePerAsset': 6}, 'LIMIT_EXCEEDED'),
             ({'kind': 'LOAD', 'seed': 'zz'}, 'INVALID_SEED')]
    for body, code in cases:
        status, problem = op.call('/api/v1/control/runs', 'POST', body)
        check('direct API refuses %s' % json.dumps(body), status == 422 and problem['code'] == code, '%s %s' % (status, problem.get('code')))
    status, problem = op.call('/api/v1/control/runs', 'POST', LOAD, console_header=False)
    check('direct API without console header refused', status == 403 and problem['code'] == 'CONSOLE_HEADER_REQUIRED', str(status))
    armed = start_run(op, dict(LOAD, durationSeconds=60))
    second = op.call('/api/v1/control/runs', 'POST', LOAD)[1]
    status, problem = op.call('/api/v1/control/runs/%s/start' % second['runId'], 'POST',
                              {'confirmToken': second['confirmToken'], 'confirmNamespace': second['namespace']})
    check('second concurrent run refused', status == 409 and problem['code'] == 'CONCURRENCY_CAP', str(status))
    status, problem = op.call('/api/v1/control/runs/%s/start' % second['runId'], 'POST',
                              {'confirmToken': 'f' * 32, 'confirmNamespace': second['namespace']})
    check('wrong confirmation token refused', status == 403 and problem['code'] == 'CONFIRM_MISMATCH', str(status))
    op.call('/api/v1/control/stop-all', 'POST')
    check('stop-all ends both', run(op, armed['runId'])['state'] == 'STOPPED' and run(op, second['runId'])['state'] == 'STOPPED')


def s_replay():
    op = operator()
    body = dict(LOAD, seed='5eed00000000002a')
    digests = []
    for attempt in range(2):
        armed = start_run(op, body)
        done = wait('completion', lambda: run(op, armed['runId'])['state'] == 'COMPLETED' and run(op, armed['runId']), 30)
        digests.append(done['sequenceDigest'])
        check('run %d digest equals the arm prediction' % (attempt + 1), done['sequenceDigest'] == armed['expectedDigest'],
              done['sequenceDigest'])
    check('same seed replays the same sequence', digests[0] == digests[1] and digests[0].startswith('200:'), digests[0])
    status, preview = op.call('/api/v1/control/preview?limit=3', 'POST', body)
    check('preview (no publication) gives the same digest', preview['digest'] == digests[0])
    log('first preview lines:', ' || '.join(preview['lines']))


def s_ttl_no_browser():
    op = operator()
    armed = start_run(op, dict(LOAD, durationSeconds=15))
    started = time.time()
    del op  # no client polls or holds the session from here on
    time.sleep(22)
    fresh = operator()
    done = run(fresh, armed['runId'])
    check('run ended by itself with no client connected', done['state'] == 'COMPLETED',
          '%s after %.0f s, stopReason=%s' % (done['state'], time.time() - started, done['stopReason']))
    check('run ended at its deadline, before its TTL', done['stoppedAt'] <= done['ttlAt'], '%s <= %s' % (done['stoppedAt'], done['ttlAt']))


def s_stop_all():
    op = operator()
    armed = start_run(op, dict(LOAD, durationSeconds=120))
    wait('emissions', lambda: run(op, armed['runId'])['emitted'] > 50, 20)
    status, result = op.call('/api/v1/control/stop-all', 'POST')
    stopped_at = sql('SELECT now()')
    check('stop-all mid-run returns the run', status == 200 and armed['runId'] in result['stopped'])
    emitted = run(op, armed['runId'])['emitted']
    time.sleep(5)
    after = run(op, armed['runId'])
    check('nothing emitted after stop-all', after['emitted'] == emitted and after['state'] == 'STOPPED', '%s emitted' % emitted)
    late = sql("SELECT count(*) FROM reading WHERE asset_id LIKE 'asset_load_%%' AND received_at > timestamptz '%s' + interval '3 seconds'" % stopped_at)
    check('no readings from the run stored 3 s after stop-all', late == '0', late)
    actions = [a['action'] for a in after['audit']]
    check('audit has ARM, START, STOP_ALL with the actor', {'ARM', 'START', 'STOP_ALL'} <= set(actions) and after['actor'] == 'operator',
          ','.join(actions))


def s_restart():
    op = operator()
    seed, first = find_seed(op, 'SUSTAINED_BREACH', dict(LOAD, kind='CHAOS', durationSeconds=300))
    log('restart scenario seed', seed, 'first injection', first.split('|I|')[1])
    armed = start_run(op, dict(LOAD, kind='CHAOS', durationSeconds=300, seed=seed))
    wait('first injection', lambda: 'INJECT' in [a['action'] for a in run(op, armed['runId'])['audit']], 45)
    log('killing the app process with SIGKILL mid-run')
    app_stop(hard=True)
    killed_at = sql('SELECT now()')
    app_start()
    restarted_at = sql('SELECT now()')
    fresh = operator()
    state = fresh.call('/api/v1/control/state')[1]
    mine = [r for r in state['openRuns'] if r['runId'] == armed['runId']]
    check('restarted pod is not executing the run', not mine or not mine[0]['executingHere'], json.dumps(mine)[:200])
    check('restarted pod producer not paused', state['readouts']['producerPaused'] is False)
    done = wait('reaper', lambda: run(fresh, armed['runId'])['state'] == 'ABORTED' and run(fresh, armed['runId']), 40)
    check('run marked ABORTED by the reaper, never resumed', 'ABORTED_RESTART' in [a['action'] for a in done['audit']], done['stopReason'])
    late = sql("SELECT count(*) FROM reading WHERE asset_id LIKE 'asset_load_%%' AND received_at > timestamptz '%s'" % restarted_at)
    check('no readings from the run after restart', late == '0', 'killed %s, restarted %s, late=%s' % (killed_at, restarted_at, late))


def s_gate():
    app_stop()
    app_start(ASSET_CHAOS_NAMESPACE_ALLOWLIST='asset-service-demo')
    op = operator()
    status, problem = op.call('/api/v1/control/runs', 'POST', dict(LOAD, kind='CHAOS'))
    check('chaos refused when the namespace is not allowlisted', status == 403 and problem['code'] == 'NAMESPACE_NOT_ALLOWLISTED',
          '%s %s' % (status, problem.get('code')))
    status, armed = op.call('/api/v1/control/runs', 'POST', LOAD)
    check('load still armable', status == 201)
    op.call('/api/v1/control/stop-all', 'POST')
    app_stop()
    app_start(ASSET_CHAOS_ENABLED='false')
    op = operator()
    status, problem = op.call('/api/v1/control/runs', 'POST', dict(LOAD, kind='CHAOS'))
    check('chaos refused when the flag is off', status == 403 and problem['code'] == 'CHAOS_DISABLED', str(status))
    app_stop()
    app_start()


def s_broker_outage():
    app_stop()
    app_start(ASSET_PRODUCER_QUEUE='200')
    op = operator()
    body = {'kind': 'LOAD', 'sites': 5, 'assetsPerSite': 10, 'metrics': ['power'], 'ratePerAsset': 1, 'durationSeconds': 120}
    armed = start_run(op, body)
    time.sleep(6)
    published_before = metric('asset_ingest_published_total')
    rss = []
    log('pausing run15-kafka for 30 s')
    subprocess.check_call(['podman', 'pause', 'run15-kafka'])
    peak = 0
    try:
        for _ in range(30):
            readouts = op.call('/api/v1/control/state')[1]['readouts']
            peak = max(peak, readouts['producerInFlight'])
            pid = open(PIDFILE).read().strip()
            child = subprocess.run(['pgrep', '-P', pid], capture_output=True, text=True).stdout.split()
            target = child[0] if child else pid
            rss.append(int(subprocess.check_output(['ps', '-o', 'rss=', '-p', target], text=True).strip() or 0))
            time.sleep(1)
    finally:
        subprocess.check_call(['podman', 'unpause', 'run15-kafka'])
    backpressure = metric('asset_ingest_rejected_total', reason='backpressure')
    check('in-flight readings stayed within the 200 bound during the outage', 0 < peak <= 200, 'peak %d' % peak)
    check('excess readings were refused with BACKPRESSURE, not queued', backpressure > 0, '%d refused' % backpressure)
    log('JVM RSS during outage (KiB): min %d max %d' % (min(rss), max(rss)))
    wait('drain', lambda: op.call('/api/v1/control/state')[1]['readouts']['producerInFlight'] == 0, 90)
    check('queue drained after the broker returned', True)
    check('queued readings were published after recovery', metric('asset_ingest_published_total') > published_before)
    check('nothing dropped (outage shorter than the 60 s delivery timeout)', metric('asset_ingest_dropped_total') == 0,
          str(metric('asset_ingest_dropped_total')))
    op.call('/api/v1/control/stop-all', 'POST')
    app_stop()
    app_start()


def s_producer_pause():
    op = operator()
    body = dict(LOAD, kind='CHAOS', durationSeconds=120)
    seed, first = find_seed(op, 'PRODUCER_PAUSE', body)
    log('producer-pause seed', seed, first.split('|I|')[1])
    armed = start_run(op, dict(body, seed=seed))
    paused = wait('producer paused', lambda: op.call('/api/v1/control/state')[1]['readouts']['producerPaused'] and
                  op.call('/api/v1/control/state')[1]['readouts'], 40)
    check('chaos paused this service\'s own producer', paused['producerPaused'], 'until %s' % paused['producerPausedUntil'])
    peak = 0
    while op.call('/api/v1/control/state')[1]['readouts']['producerPaused']:
        peak = max(peak, op.call('/api/v1/control/state')[1]['readouts']['producerInFlight'])
        time.sleep(0.5)
    check('queue bounded while paused', peak <= 2000, 'peak in flight %d of 2000' % peak)
    wait('drain', lambda: op.call('/api/v1/control/state')[1]['readouts']['producerInFlight'] == 0, 30)
    check('producer resumed by itself and drained', True)
    op.call('/api/v1/control/reset', 'POST')


def s_flap_chaos():
    op = operator()
    body = dict(LOAD, kind='CHAOS', durationSeconds=90)
    seed, first = find_seed(op, 'FLAP', body)
    marker = first.split('|I|')[1]
    target = marker.split()[1]
    asset, metric_name = target.split('/')
    log('flap seed', seed, marker)
    before = sql("SELECT count(*) FROM alert WHERE asset_id = '%s' AND metric_name = '%s'" % (asset, metric_name))
    armed = start_run(op, dict(body, seed=seed))
    wait('flap injection', lambda: 'INJECT' in [a['action'] for a in run(op, armed['runId'])['audit']], 40)
    end_ms = int(marker.split()[2].split('-')[1].replace('ms', ''))
    time.sleep(end_ms / 1000.0 - 5 + 8)
    rows = wait('alert cleared', lambda: (lambda r: r if r and r.split('|')[1] == 'CLEARED' else None)(
        sql("SELECT count(*) || '|' || coalesce(max(status),'') FROM alert WHERE asset_id = '%s' AND metric_name = '%s'"
            " AND activated_at > (SELECT started_at FROM control_run WHERE run_id = '%s')" % (asset, metric_name, armed['runId']))), 40)
    check('flapping chaos gave exactly one alert, then one clear', rows.startswith('1|CLEARED'), rows + ' (before: %s)' % before)
    op.call('/api/v1/control/stop-all', 'POST')


def s_rejections():
    """Each invalid chaos entry goes through the shared validator and is refused, never published."""
    op = operator()
    body = dict(LOAD, kind='CHAOS', durationSeconds=60)
    expected = {'INVALID_UNIT': ['invalid_unit'], 'INVALID_PAYLOAD': ['missing_field', 'not_finite', 'out_of_bounds', 'unknown_metric'],
                'OVERSIZE_PAYLOAD': ['oversize']}
    for entry, reasons in expected.items():
        seed, first = find_seed(op, entry, body)
        before = {r: metric('asset_ingest_rejected_total', reason=r, source='chaos') for r in reasons}
        published_before = metric('asset_ingest_published_total')
        armed = start_run(op, dict(body, seed=seed))
        wait('injection', lambda: 'INJECT' in [a['action'] for a in run(op, armed['runId'])['audit']], 45)
        time.sleep(1)
        op.call('/api/v1/control/stop-all', 'POST')
        after = {r: metric('asset_ingest_rejected_total', reason=r, source='chaos') for r in reasons}
        delta = {r: after[r] - before[r] for r in reasons}
        check('%s readings refused by the validator (%s)' % (entry, first.split('|I|')[1].strip()), sum(delta.values()) > 0,
              json.dumps(delta))
        check('%s run still published its valid readings' % entry, metric('asset_ingest_published_total') > published_before)


SCENARIOS = {'access': s_access, 'caps': s_caps, 'replay': s_replay, 'ttl': s_ttl_no_browser, 'stopall': s_stop_all,
             'restart': s_restart, 'gate': s_gate, 'outage': s_broker_outage, 'pause': s_producer_pause, 'flap': s_flap_chaos,
             'rejections': s_rejections}


def s_db_outage():
    """Review OPS-4: with the database down nobody can stop a run, so the pod stops its own runs."""
    op = operator()
    armed = start_run(op, dict(LOAD, durationSeconds=300))
    wait('emissions', lambda: run(op, armed['runId'])['emitted'] > 20, 20)
    log('pausing run15-pg for 45 s')
    subprocess.check_call(['podman', 'pause', 'run15-pg'])
    try:
        time.sleep(32)
        before = metric('asset_ingest_admitted_total', source='load')
        time.sleep(10)
        after = metric('asset_ingest_admitted_total', source='load')
        check('run stopped emitting after heartbeats failed past 20 s', after == before, 'admitted %.0f -> %.0f' % (before, after))
    finally:
        subprocess.check_call(['podman', 'unpause', 'run15-pg'])
    fresh = operator()
    done = wait('reaper', lambda: (lambda r: r if r['state'] in ('ABORTED', 'STOPPED') else None)(run(fresh, armed['runId'])), 40)
    check('the run is closed in the database after the outage', done['state'] == 'ABORTED', done['stopReason'])


def s_burst():
    """Review ARCH-2: a burst cannot push a run past its own rate cap."""
    op = operator()
    body = {'kind': 'CHAOS', 'sites': 2, 'assetsPerSite': 10, 'metrics': ['power'], 'ratePerAsset': 1, 'durationSeconds': 60}
    seed, first = find_seed(op, 'BURST', body, accept=lambda marker: int(marker.split()[3].replace('x', '')) >= 3)
    log('burst seed', seed, first.split('|I|')[1])
    start_ms = int(first.split('|')[1])
    armed = start_run(op, dict(body, seed=seed))
    before = metric('asset_ingest_admitted_total', source='chaos')
    t0 = time.time()
    time.sleep(start_ms / 1000.0 + 6)
    admitted = metric('asset_ingest_admitted_total', source='chaos') - before
    elapsed = time.time() - t0
    capped = metric('asset_ingest_rejected_total', source='chaos', reason='run_rate') + metric('asset_ingest_rejected_total', source='chaos', reason='rate_limited')
    check('admitted rate during the burst stayed within the 50/s run cap', admitted / elapsed <= 52, '%.1f/s over %.0f s' % (admitted / elapsed, elapsed))
    check('burst excess was refused by the rate caps', capped > 0, '%d refused' % capped)
    op.call('/api/v1/control/stop-all', 'POST')


SCENARIOS.update({'dboutage': s_db_outage, 'burst': s_burst})

if __name__ == '__main__':
    for name in sys.argv[1:]:
        log('=== scenario', name)
        try:
            SCENARIOS[name]()
        except Exception as error:  # report and continue with the next scenario
            check('scenario %s completed' % name, False, repr(error)[:300])
    log('failures:', check.failures)
