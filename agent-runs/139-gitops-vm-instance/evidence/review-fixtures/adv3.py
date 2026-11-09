exec(open('adv.py').read().split("f,_=ci(base); run")[0])
f,r=ci("""url: https://github.com/box1-org/site-gateway
git_provider:
  pipelinerun_provenance: default_branch
settings:
  pipelinerun_provenance: source
"""); run('decoy provenance under git_provider, real settings=source', f); print(r)
f,r=ci("""url: https://github.com/box1-org/site-gateway
settings:
  pipelinerun_provenance: default_branch
  github_app_token_scope_repos: [box1-org/box1-gitops]
"""); run('flow-style scope list', f)
