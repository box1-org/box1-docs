#!/usr/bin/env python3
"""Run box1-gitops-validate's ci/<repo> rule (box1-docs#139) and its target discovery
against the ci/ bundles rendered by box1-templates' quarkus-monorepo template.

Usage: check-ci-bundles.py <box1-gitops checkout> <box1-templates checkout>
(after `npm run validate` in box1-templates). Needs kubectl.
"""
import pathlib, shutil, subprocess, sys, tempfile
gitops, templates = map(pathlib.Path, sys.argv[1:3])
text = (gitops / 'platform/pipelines/tasks/gitops-validate.yaml').read_text()
start = text.index('    script: |')
body = []
for line in text[start:].splitlines()[1:]:
    if line and not line.startswith('      '):
        break
    body.append(line[6:] if line else '')
ns = {'__name__': 'box1_ci_check'}
exec(compile('\n'.join(body), 'gitops-validate.yaml', 'exec'), ns)
rendered = sorted((templates / '.validation/quarkus-monorepo').glob('*/gitops'))
assert rendered, 'run npm run validate in box1-templates first'
for root in rendered:
    for ci in sorted((root / 'ci').iterdir()):
        repo = ci.name
        ns['check_ci'](repo, subprocess.check_output(['kubectl', 'kustomize', str(ci)], text=True))
        # The same discovery the Task uses on a box1-workloads-dev checkout.
        with tempfile.TemporaryDirectory() as checkout:
            checkout = pathlib.Path(checkout)
            shutil.copytree(root / 'ci', checkout / 'ci')
            (checkout / 'workloads' / 'placeholder').mkdir(parents=True)
            (checkout / 'workloads' / 'placeholder' / 'kustomization.yaml').write_text('resources: []\n')
            _, targets = ns['validation_targets'](checkout)
            assert [t.parent.name for t in targets] == [repo]
            (checkout / 'workloads' / repo).mkdir()
            try:
                ns['validation_targets'](checkout)
                raise SystemExit('collision not detected')
            except AssertionError as error:
                assert 'collides with workloads/' in str(error)
        print('PASS check_ci and target discovery: ci/' + repo)
