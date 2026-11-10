exec(open('adv.py').read().split("repo='site-gateway'")[0])
name,files=t.instance_bundle()
def cm(data):
    f=dict(files); f['site.yaml']="apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: site-west-site\n  namespace: site-west-dev\ndata:\n"+textwrap.indent(data,'  ')
    r=render(f); return lambda: v['validate']('site-west',r)
run('baseline instance', cm("siteId: x\n"))
run('embedded password in file value', cm("gateway.yaml: |\n  admin_password: hunter2\n  client_secret: abc\n"))
run('kubeconfig key', cm("kubeconfig: |\n  users:\n  - user: {token: abc}\n"))
run('bearer/auth/cert keys', cm("bearer: abc\nauth: abc\nclient.crt: abc\nclientCertKey: x\n"))
run('UPPER key PASSWORD', cm("ADMIN_PASSWORD: x\n"))
run('credential in env-style value', cm("settings.env: 'PASSWORD=hunter2'\n"))
# extra non-ConfigMap kind carrying data
f=dict(files); f['x.yaml']="apiVersion: v1\nkind: ConfigMapList\nitems: []\n"
f['kustomization.yaml']=files['kustomization.yaml']+"  - x.yaml\n"
try:
    r=render(f); run('ConfigMapList', lambda: v['validate']('site-west',r))
except Exception as e: print('render err', e)
# cloudInitConfigDrive secretRef to the admin ssh secret
f=dict(files); f['virtualmachine.yaml']=files['virtualmachine.yaml'].replace("""                - name: cloudinitdisk
                  cloudInitNoCloud:""","""                - name: cd
                  cloudInitConfigDrive:
                    secretRef:
                      name: site-west-other
                - name: cloudinitdisk
                  cloudInitNoCloud:""")
r=render(f); run('extra cloudInitConfigDrive with secretRef to another (out-of-git) secret', lambda: v['validate']('site-west',r))
