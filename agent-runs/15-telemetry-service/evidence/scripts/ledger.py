"""Rewrites requirements.yaml from one table so the ledger stays consistent. Run from the run-state directory."""
import json
import sys

P = 'src/main/java/org/box1/asset/'
T = 'src/test/java/org/box1/asset/'
DEFAULT = './mvnw verify'
CONT = './mvnw verify -Pcontainers'
EV3 = 'evidence/03-tests-local.txt'
L = {}


def req(rid, status, impl, tests, commands, evidence, limitations=()):
    L[rid] = dict(status=status, implementation=impl, tests=tests, commands=commands, evidence=evidence,
                  limitations=list(limitations))


req('TEL-INGEST-001', 'locally_tested', [P + 'ingest/IngestionPipeline.java', P + 'domain/ReadingValidator.java', P + 'ingest/TokenBucket.java'],
    [T + 'ReadingValidatorTest.java', T + 'SecurityTest.java', T + 'TokenBucketTest.java'], [DEFAULT], [EV3])
req('TEL-INGEST-002', 'locally_tested', [P + 'ingest/IngestionPipeline.java', P + 'ingest/Envelopes.java'],
    [T + 'ContractTest.java', T + 'it/TelemetryFlowTest.java'], [DEFAULT, CONT], [EV3])
req('TEL-INGEST-003', 'locally_tested', [P + 'store/TelemetryStore.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'],
    [T + 'it/TelemetryFlowTest.java#burstWithDuplicatesStoresEachReadingOnceAndPagesStably'], [CONT], [EV3])
req('TEL-STORE-001', 'implemented', [P + 'ops/RetentionJob.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'], [], [], [],
    ['Retention deletes not yet exercised by a test'])
req('TEL-READ-001', 'locally_tested', [P + 'api/ReadingsResource.java', P + 'api/Cursors.java'],
    [T + 'it/TelemetryFlowTest.java#burstWithDuplicatesStoresEachReadingOnceAndPagesStably'], [CONT], [EV3])
req('TEL-ALERT-001', 'locally_tested', [P + 'api/ReadingsResource.java'], [T + 'it/TelemetryFlowTest.java'], [CONT], [EV3])
req('TEL-ALERT-002', 'locally_tested', [P + 'domain/ThresholdEngine.java', P + 'consume/ReadingProjector.java'],
    [T + 'ThresholdEngineTest.java', T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [DEFAULT, CONT], [EV3])
req('TEL-ALERT-003', 'locally_tested', [P + 'consume/ReadingProjector.java', P + 'ops/OutboxRelay.java'],
    [T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [CONT], [EV3])
req('TEL-BP-001', 'locally_tested', [P + 'ingest/ReadingPublisher.java'], [T + 'ReadingPublisherTest.java'], [DEFAULT], [EV3],
    ['Unit-tested with MockProducer; a real broker pause is a Phase 4 scenario'])
req('TEL-DLQ-001', 'locally_tested', [P + 'consume/ReadingConsumer.java', P + 'consume/EventParser.java', P + 'consume/Failures.java'],
    [T + 'it/TelemetryFlowTest.java#poisonRecordsGoToTheDeadLetterTopicAndConsumptionContinues', T + 'FailuresTest.java'], [CONT], [EV3],
    ['Needs topic box1.telemetry.dlq.v1 on the cluster (D-012)'])
req('TEL-OBS-001', 'implemented', [P + 'ops/OperationalGauges.java', P + 'ops/Readouts.java'], [], [], [],
    ['Metric names listed in docs/architecture.md; trace export off until box1-docs#22'])
req('TEL-OBS-002', 'locally_tested', [P + 'consume/ReadingConsumer.java', P + 'consume/ReadingProjector.java'],
    [T + 'it/TelemetryFlowTest.java#flappingGivesOneAlertOneEventThenOneClearWithLinkedIds'], [CONT], [EV3])
req('TEL-SEC-001', 'locally_tested', ['src/main/resources/application.properties'], [T + 'SecurityTest.java'], [DEFAULT], [EV3])
req('TEL-CON-001', 'implemented', ['src/main/resources/META-INF/resources/console/'], [], [], [])
req('TEL-CON-002', 'locally_tested', ['src/main/resources/application.properties', P + 'api/ControlResource.java'],
    [T + 'SecurityTest.java#consoleAndControlNeedABrowserLoginAndNeverAcceptAnonymousOrBearerAlone'], [DEFAULT], [EV3],
    ['Real Keycloak login is a Phase 4 scenario; live needs D-013'])
req('TEL-LOAD-001', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunScript.java'], [T + 'it/ControlTest.java'], [CONT], [EV3])
req('TEL-LOAD-002', 'locally_tested', [P + 'control/SeededRandom.java', P + 'control/RunScript.java', P + 'control/SequenceDigest.java'],
    [T + 'RunScriptTest.java', T + 'it/ControlTest.java#sameSeedReplaysTheSameSequenceAndRunsEndWithoutABrowser'], [DEFAULT, CONT], [EV3])
req('TEL-CHAOS-001', 'locally_tested', [P + 'control/ChaosEntry.java', P + 'control/RunScript.java'],
    [T + 'RunScriptTest.java#chaosUsesOnlyTheCatalogWithinItsBounds', T + 'it/ControlTest.java#chaosRunsInjectOnlyCatalogEntriesAndStopAllResumesTheProducer'], [DEFAULT, CONT], [EV3])
req('TEL-CHAOS-002', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunTransitions.java', P + 'api/ConsoleHeaderFilter.java'],
    [T + 'it/ControlTest.java#capsHoldAgainstRequestsThatBypassThePage', T + 'it/ControlTest.java#armThenConfirmWithTokenAndTypedNamespaceThenConcurrencyCapThenStopAll'], [CONT], [EV3])
req('TEL-CHAOS-003', 'locally_tested', [P + 'control/RunManager.java'], [T + 'it/ControlTest.java#armThenConfirmWithTokenAndTypedNamespaceThenConcurrencyCapThenStopAll'], [CONT], [EV3])
req('TEL-CHAOS-004', 'locally_tested', [P + 'control/RunStore.java', 'src/main/resources/db/migration/V1__telemetry_schema.sql'], [T + 'it/ControlTest.java'], [CONT], [EV3])
req('TEL-CHAOS-005', 'locally_tested', [P + 'control/RunTransitions.java#reap'], [T + 'it/ControlTest.java#reaperAbortsRunsWhoseOwnerStoppedAndExpiresRunsPastTtl'], [CONT], [EV3],
    ['Simulated with a stale row; a real process kill is a Phase 4 scenario'])
req('TEL-CHAOS-006', 'implemented', ['src/main/resources/META-INF/resources/console/console.js'], [], [], [])
req('TEL-CHAOS-007', 'locally_tested', [P + 'control/RunManager.java', P + 'control/RunTransitions.java#reap'],
    [T + 'it/ControlTest.java#sameSeedReplaysTheSameSequenceAndRunsEndWithoutABrowser', T + 'it/ControlTest.java#reaperAbortsRunsWhoseOwnerStoppedAndExpiresRunsPastTtl'], [CONT], [EV3])
req('TEL-GATE-001', 'locally_tested', [P + 'control/ChaosGate.java'], [T + 'ChaosGateTest.java', T + 'it/GateNotAllowlistedTest.java', T + 'it/GateDisabledTest.java'], [DEFAULT, CONT], [EV3],
    ['The namespace to allowlist is open (D-015)'])
req('TEL-UX-001', 'implemented', ['src/main/resources/META-INF/resources/console/'], [], [], [], ['Brand mark open (D-016)'])
req('TEL-UX-002', 'implemented', [P + 'ops/Readouts.java'], [], [], [])
req('TEL-SMOKE-001', 'locally_tested', [P + '../GreetingResource.java'], [T + 'SecurityTest.java#goldenPathSmokePathsStayPublic'], [DEFAULT], [EV3])
req('TEL-CONTRACT-001', 'locally_tested', ['box1-ops-contracts: events/v1/equipment.threshold-exceeded.schema.json, openapi/asset-service.yaml'],
    [T + 'ContractTest.java', T + 'OpenApiContractTest.java', 'box1-ops-contracts npm test / npm run validate'], [DEFAULT, 'npm test && npm run validate'], [EV3],
    ['Contracts PR not merged; pinned to branch commit'])
req('TEL-DOC-001', 'implemented', ['README.md', 'docs/architecture.md', 'docs/runbook.md'], [], [], [])
req('TEL-DEL-001', 'proposed', [], [], [], [], ['Needs merges and approvals'])
req('TEL-LIVE-001', 'proposed', [], [], [], [], ['Needs D-012 to D-015 and approval'])

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
