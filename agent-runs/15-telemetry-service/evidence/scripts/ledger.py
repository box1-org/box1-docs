"""Rewrites requirements.yaml from one table so the ledger stays consistent. Run from the run-state directory."""
import json
import sys

P = 'src/main/java/org/box1/asset/'
T = 'src/test/java/org/box1/asset/'
DEFAULT = './mvnw -B clean verify -DskipITs=false'
CONT = './mvnw clean verify -Pcontainers'
EV3 = 'evidence/03-tests-local.txt'
EV7 = 'evidence/07-review-repairs-local.txt'
L = {}


def req(rid, status, impl, tests, commands, evidence, limitations=()):
    L[rid] = dict(status=status, implementation=impl, tests=tests, commands=commands, evidence=evidence,
                  limitations=list(limitations))


req('TEL-INGEST-001', 'locally_tested', [P + 'ingest/IngestionPipeline.java', P + 'domain/ReadingValidator.java', P + 'ingest/TokenBucket.java'],
    [T + 'ReadingValidatorTest.java', T + 'SecurityTest.java', T + 'TokenBucketTest.java'], [DEFAULT], [EV3])
req('TEL-INGEST-002', 'locally_tested', [P + 'ingest/IngestionPipeline.java', P + 'ingest/Envelopes.java'],
    [T + 'ContractTest.java', T + 'it/TelemetryFlowTest.java'], [DEFAULT, CONT], [EV3])
req('TEL-INGEST-003', 'locally_tested', [P + 'store/TelemetryStore.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'],
    [T + 'it/TelemetryFlowTest.java#burstWithDuplicatesStoresEachReadingOnceAndPagesStably'], [CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-STORE-001', 'locally_tested', [P + 'ops/RetentionJob.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'], [T + 'it/RetentionTest.java'], [CONT], [EV3],
    ['Row-cap branch not exercised; age retention and audit guard are'])
req('TEL-READ-001', 'locally_tested', [P + 'api/ReadingsResource.java', P + 'api/Cursors.java'],
    [T + 'it/TelemetryFlowTest.java#burstWithDuplicatesStoresEachReadingOnceAndPagesStably'], [CONT], [EV3])
req('TEL-ALERT-001', 'locally_tested', [P + 'api/ReadingsResource.java'], [T + 'it/TelemetryFlowTest.java'], [CONT], [EV3])
req('TEL-ALERT-002', 'locally_tested', [P + 'domain/ThresholdEngine.java', P + 'consume/ReadingProjector.java'],
    [T + 'ThresholdEngineTest.java', T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [DEFAULT, CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-ALERT-003', 'locally_tested', [P + 'consume/ReadingProjector.java', P + 'ops/OutboxRelay.java'],
    [T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [CONT], [EV3])
req('TEL-BP-001', 'locally_tested', [P + 'ingest/ReadingPublisher.java'], [T + 'ReadingPublisherTest.java'], [DEFAULT], [EV3, 'evidence/04-scenarios-local.txt'],
    [])
req('TEL-DLQ-001', 'locally_tested', [P + 'consume/ReadingConsumer.java', P + 'consume/EventParser.java', P + 'consume/Failures.java'],
    [T + 'it/TelemetryFlowTest.java#poisonRecordsGoToTheDeadLetterTopicAndConsumptionContinues', T + 'FailuresTest.java'], [CONT], [EV3],
    ['Needs topic box1.telemetry.dlq.v1 on the cluster (D-012)'])
req('TEL-OBS-001', 'locally_tested', [P + 'ops/OperationalGauges.java', P + 'ops/Readouts.java'], ['scripts/scenarios.py (outage, pause, rejections read /q/metrics and readouts)'], ['python3 -I scenarios.py outage pause rejections'], ['evidence/04-scenarios-local.txt'],
    ['Trace export off until box1-docs#22; stale-asset gauge observed but not asserted'])
req('TEL-OBS-002', 'locally_tested', [P + 'consume/ReadingConsumer.java', P + 'consume/ReadingProjector.java'],
    [T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [CONT], [EV3])
req('TEL-SEC-001', 'locally_tested', ['src/main/resources/application.properties'], [T + 'SecurityTest.java'], [DEFAULT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-CON-001', 'locally_tested', ['src/main/resources/META-INF/resources/console/'], ['scripts/console-check.mjs'], ['node console-check.mjs'], ['evidence/05-browser-local.txt'])
req('TEL-CON-002', 'locally_tested', ['src/main/resources/application.properties', P + 'api/ControlResource.java'],
    [T + 'SecurityTest.java#consoleAndControlNeedABrowserLoginAndNeverAcceptAnonymousOrBearerAlone'], [DEFAULT], [EV3, 'evidence/04-scenarios-local.txt'],
    ['Local Keycloak 26.4, not RH-SSO 7.6; live needs D-013'])
req('TEL-LOAD-001', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunScript.java'], [T + 'it/ControlTest.java'], [CONT], [EV3])
req('TEL-LOAD-002', 'locally_tested', [P + 'control/SeededRandom.java', P + 'control/RunScript.java', P + 'control/SequenceDigest.java'],
    [T + 'RunScriptTest.java', T + 'it/ControlTest.java#sameSeedReplaysTheSameSequenceAndRunsEndWithoutABrowser'], [DEFAULT, CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-CHAOS-001', 'locally_tested', [P + 'control/ChaosEntry.java', P + 'control/RunScript.java'],
    [T + 'RunScriptTest.java#chaosUsesOnlyTheCatalogWithinItsBounds', T + 'it/ControlTest.java#chaosRunsInjectOnlyCatalogEntriesAndStopAllResumesTheProducer'], [DEFAULT, CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-CHAOS-002', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunTransitions.java', P + 'api/ConsoleHeaderFilter.java'],
    [T + 'it/ControlTest.java#capsHoldAgainstRequestsThatBypassThePage', T + 'it/ControlTest.java#armThenConfirmWithTokenAndTypedNamespaceThenConcurrencyCapThenStopAll'], [CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-CHAOS-003', 'locally_tested', [P + 'control/RunManager.java'], [T + 'it/ControlTest.java#armThenConfirmWithTokenAndTypedNamespaceThenConcurrencyCapThenStopAll'], [CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-CHAOS-004', 'locally_tested', [P + 'control/RunStore.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'], [T + 'it/ControlTest.java'], [CONT], [EV3])
req('TEL-CHAOS-005', 'locally_tested', [P + 'control/RunTransitions.java#reap'], [T + 'it/ControlTest.java#reaperAbortsRunsWhoseOwnerStoppedAndExpiresRunsPastTtl'], [CONT], [EV3, 'evidence/04-scenarios-local.txt'],
    [])
req('TEL-CHAOS-006', 'locally_tested', ['src/main/resources/META-INF/resources/console/console.js'], ['scripts/console-check.mjs (state calls aborted)'], ['node console-check.mjs'], ['evidence/05-browser-local.txt', 'evidence/screenshots/06-unknown-state.png'])
req('TEL-CHAOS-007', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunTransitions.java#reap'],
    [T + 'it/ControlTest.java#sameSeedReplaysTheSameSequenceAndRunsEndWithoutABrowser', T + 'it/ControlTest.java#reaperAbortsRunsWhoseOwnerStoppedAndExpiresRunsPastTtl'], [CONT], [EV3, 'evidence/04-scenarios-local.txt'])
req('TEL-GATE-001', 'locally_tested', [P + 'control/ChaosGate.java'], [T + 'ChaosGateTest.java', T + 'it/GateNotAllowlistedTest.java', T + 'it/GateDisabledTest.java'], [DEFAULT, CONT], [EV3, 'evidence/04-scenarios-local.txt'],
    ['The namespace to allowlist is open (D-015)'])
req('TEL-UX-001', 'locally_tested', ['src/main/resources/META-INF/resources/console/'], ['scripts/console-check.mjs'], ['node console-check.mjs'], ['evidence/05-browser-local.txt', 'evidence/screenshots/'], ['Brand mark open (D-016): text wordmark only'])
req('TEL-UX-002', 'locally_tested', [P + 'ops/Readouts.java'], ['scripts/console-check.mjs', 'scripts/scenarios.py'], ['node console-check.mjs'], ['evidence/05-browser-local.txt', 'evidence/screenshots/03-running-chaos.png'])
req('TEL-SMOKE-001', 'locally_tested', [P + '../GreetingResource.java'], [T + 'SecurityTest.java#goldenPathSmokePathsStayPublic'], [DEFAULT], [EV3])
req('TEL-CONTRACT-001', 'locally_tested', ['box1-ops-contracts: events/v1/equipment.threshold-exceeded.schema.json, openapi/asset-service.yaml'],
    [T + 'ContractTest.java', T + 'OpenApiContractTest.java', 'box1-ops-contracts npm test / npm run validate'], [DEFAULT, 'npm test && npm run validate'], [EV3],
    ['Contracts PR not merged; pinned to branch commit'])
req('TEL-DOC-001', 'implemented', ['README.md', 'docs/architecture.md', 'docs/runbook.md'], [], [], [])
req('TEL-DEL-001', 'proposed', [], [], [], [], ['Needs merges and approvals'])
req('TEL-LIVE-001', 'proposed', [], [], [], [], ['Needs D-012 to D-015 and approval'])

for _rid in L:
    if L[_rid]['status'] == 'locally_tested' and EV7 not in L[_rid]['evidence']:
        L[_rid]['evidence'].append(EV7)
L['TEL-READ-001']['limitations'].append('Reads need telemetry-reader, telemetry-writer or chaos-operator (SEC-2)')
L['TEL-BP-001']['limitations'] = ['Catch-up memory not measured (OPS-11)']
L['TEL-CHAOS-002']['tests'].append('scripts/scenarios.py burst (actual rate incl. bursts)')
L['TEL-CHAOS-005']['tests'].append('scripts/scenarios.py dboutage (fail-safe without the database)')
L['TEL-CON-002']['limitations'].append('Cluster login (https redirect, RH-SSO 7.6) not exercised')

EV8 = 'evidence/08-ci.txt'
CI_NOTE = 'ci_verified covers only the container-free tests in CI; the rest of the proof is local'
for _rid in ['TEL-INGEST-001', 'TEL-INGEST-002', 'TEL-ALERT-002', 'TEL-BP-001', 'TEL-LOAD-002', 'TEL-CHAOS-001', 'TEL-GATE-001',
             'TEL-SEC-001', 'TEL-SMOKE-001', 'TEL-CONTRACT-001']:
    L[_rid]['status'] = 'ci_verified'
    L[_rid]['evidence'].append(EV8)
    L[_rid]['commands'] = list(dict.fromkeys(L[_rid]['commands'] + ['CI asset-service-validate-zr7tn at 11fa5a1']))
    L[_rid]['limitations'].append(CI_NOTE)

EV10 = 'evidence/10-delivery.txt'
DEPLOY = {'image_digest': 'sha256:6d8e8c172b2885f35a551eb34c53429e1ac85a1771263ba841795c683fbde944',
          'gitops_commit': '7a90162e4ed31aba2fa9e98e07bc765d321c30d9', 'source': '1706dd0b0123cbddd510d1fb6bf9d44cc020fee5'}
for _rid, _e in L.items():
    if _rid in ('TEL-LIVE-001',):
        continue
    if _e['status'] in ('locally_tested', 'ci_verified', 'implemented', 'proposed'):
        _e['status'] = 'deployed'
    _e['deployment'] = DEPLOY
    _e['evidence'].append(EV10)
for _rid, _why in {
        'TEL-SEC-001': 'anonymous POST /api/v1/telemetry/readings through the Route: 401',
        'TEL-SMOKE-001': 'release smoke passed against the Route',
        'TEL-DEL-001': 'gate pass, promotion #72, Argo Synced/Healthy at 7a90162e, pod imageID = release digest',
        'TEL-GATE-001': 'live pod reports chaos gate CHAOS_DISABLED with the flag off (negative case only)',
        'TEL-STORE-001': 'Flyway V1 applied on the cluster database (retention job not observed live)'}.items():
    L[_rid]['status'] = 'live_verified'
    L[_rid]['commands'].append('read-only live checks, evidence/10')
    L[_rid]['limitations'].append('live: ' + _why)
L['TEL-CON-002']['limitations'].append('live: anonymous 302/499 verified; operator login with the role not yet exercised on the cluster')
L['TEL-LIVE-001']['status'] = 'proposed'
L['TEL-LIVE-001']['limitations'] = ['Seeded load run: user will drive the console', 'Random chaos run on the cluster: blocked by D-015 (deferred by the user)']

if __name__ == '__main__':
    updates = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    for rid, change in updates.items():
        L[rid].update(change)
    lines = open('requirements.yaml').read().split('\n- id: ')
    head, entries = lines[0], lines[1:]
    out = [head.rstrip('\n') + '\n']
    for entry in entries:
        rid = entry.split('\n', 1)[0].strip()
        desc = [l for l in entry.split('\n') if l.startswith('  description:')][0]
        e = L[rid]
        dep = e.get('deployment', {})
        out.append('- id: %s\n%s\n  status: %s\n  implementation: %s\n  tests: %s\n  commands: %s\n  evidence: %s\n  deployment: %s\n  limitations: %s\n' % (
            rid, desc, e['status'], json.dumps(e['implementation']), json.dumps(e['tests']), json.dumps(e['commands']),
            json.dumps(e['evidence']), json.dumps(dep), json.dumps(e['limitations'])))
    open('requirements.yaml', 'w').write('\n'.join(out))
    from collections import Counter
    print(Counter(e['status'] for e in L.values()))
