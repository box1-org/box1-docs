#!/usr/bin/env python3
"""Package an already-built multi-module application with box1-maven-bundle's own
functions (extracted from the Task YAML), without Maven or a registry.

Usage: bundle-local.py <maven-bundle.yaml> <application dir> <out dir> <revision>
Prints the modules and the OCI manifest digest; writes <out>/bundle and <out>/oci.
"""
import pathlib, sys
task, application, out, revision = sys.argv[1:5]
text = pathlib.Path(task).read_text()
start = text.index('    script: |', text.index('  - name: verify-and-package\n'))
body = []
for line in text[start:].splitlines()[1:]:
    if line and not line.startswith('      '):
        break
    body.append(line[6:] if line else '')
ns = {'__name__': 'box1_local'}
exec(compile('\n'.join(body), task, 'exec'), ns)
app, out = pathlib.Path(application), pathlib.Path(out)
modules = ns['modules_of']((app / 'pom.xml').read_text())
ns['stage'](app, modules, out / 'bundle')
print('modules', ','.join(modules))
print('digest', ns['make_layout'](out / 'bundle', out / 'oci', revision, 'box1-org/site-gateway', modules))
