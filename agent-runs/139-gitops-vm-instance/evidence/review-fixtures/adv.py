import sys, os, pathlib, subprocess, tempfile, textwrap
G='<work>/box1-gitops/platform/pipelines/tasks'
sys.path.insert(0,G)
import importlib.util
spec=importlib.util.spec_from_file_location('t',G+'/test-gitops-validate.py'); t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
v=t.load_validator()
def render(files):
    d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
    for n,c in files.items(): pathlib.Path(d,n).write_text(textwrap.dedent(c).lstrip())
    return subprocess.check_output(['kubectl','kustomize',d],text=True)
def run(label, fn):
    try: fn(); print('PASS (accepted):',label)
    except AssertionError as e: print('REJECTED:',label,'->',e)
    except subprocess.CalledProcessError as e: print('RENDER FAIL:',label)
repo='site-gateway'
def ci(repo_spec, extra=None):
    files={'kustomization.yaml':'resources:\n- repository.yaml\n'+('- extra.yaml\n' if extra else ''),
           'repository.yaml':'apiVersion: pipelinesascode.tekton.dev/v1alpha1\nkind: Repository\nmetadata:\n  name: site-gateway\n  namespace: box1-ci\nspec:\n'+textwrap.indent(textwrap.dedent(repo_spec),'  ')}
    if extra: files['extra.yaml']=extra
    r=render(files); return lambda: v['check_ci'](repo,r), r
base="""url: https://github.com/box1-org/site-gateway
settings:
  pipelinerun_provenance: default_branch
"""
f,_=ci(base); run('baseline repo', f)
f,_=ci(base+"""params:
- name: tok
  secret_ref:
    name: box1-gitops-token
    key: git-provider-token
"""); run('Repository params.secret_ref exposes box1-ci Secret', f)
f,_=ci(base+"""git_provider:
  url: https://evil.example.com
  secret:
    name: box1-gitops-token
    key: git-provider-token
"""); run('Repository git_provider secret to foreign url', f)
f,r=ci("""url: https://github.com/box1-org/site-gateway
incoming:
- type: webhook-url
  secret:
    name: x
  targets: [main]
  pipelinerun_provenance: default_branch
settings:
  pipelinerun_provenance: source
"""); run('decoy provenance under incoming, real settings=source', f)
f,r=ci("""url: https://github.com/box1-org/site-gateway
git_provider:
  github_app_token_scope_repos:
  - box1-org/harmless
settings:
  pipelinerun_provenance: default_branch
  github_app_token_scope_repos:
  - box1-org/box1-workloads-dev
"""); run('decoy token scope before real settings scope to box1-workloads-dev', f); print(r)
role="""apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: site-gateway-r
  namespace: box1-ci
rules:
- apiGroups: [""]
  resources: ["%s"]
  resourceNames: ["%s"]
  verbs: [%s]
"""
for res,nm,vb in [('*/status','x','"get"'),('pods/exec','some-pod','"get"'),('services/proxy','el-listener','"get"'),('serviceaccounts','pipeline','"get"'),('configmaps','x','"get","list"')]:
    f,_=ci(base, role%(res,nm,vb)); run('Role %s %s %s'%(res,nm,vb), f)
# list kind smuggle in ci
f,_=ci(base,"""apiVersion: v1
kind: List
items:
- apiVersion: v1
  kind: Secret
  metadata: {name: site-gateway-s, namespace: box1-ci}
  stringData: {a: b}
"""); run('kind List wrapping Secret', f)
