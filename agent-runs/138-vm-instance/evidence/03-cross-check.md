# Cross-check: plugin bundle against the box1-gitops validator and promote Task

Both scripts were run from a scratchpad, against the templates render in `.validation/vm-instance/<name>`:
- `promote.cjs` applies the plugin's `vm-instance` first promotion, with no network access.
- `check.py` loads `box1-gitops-validate` and `box1-gitops-promote` from a checkout.

## Against box1-gitops `golden-path/138-vm-instance` @ `2030fcb`

```text
site-west site-west -> vm-instance     (unbuilt onboarding bundle)
site-west promoted -> vm-instance      (after the plugin's first promotion)
site-east site-east -> vm-instance
site-east promoted -> vm-instance
day-2 promote files: ['workloads/site-east/virtualmachine.yaml']
```

The first promotion's PR files are `workloads/<name>/{datavolume,kustomization,virtualmachine}.yaml` only. A day-2 `plan_instance_updates` call (#139) changes only that instance's `virtualmachine.yaml`. This is evidence for "promoting one instance leaves the other unchanged" at the file level only; it was **not** observed live.

## Against the #133 head `59e1ef0` (#139 rules as written)

```text
AssertionError: ConfigMap site-west-site must not hold credentials; found keycloakTokenUrl. …
```

So box1-gitops#134 must merge before the first instance onboarding (D-007).
