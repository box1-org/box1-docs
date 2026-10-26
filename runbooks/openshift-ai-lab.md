# OpenShift AI lab on Box1

Validated October 25, 2026, America/New_York, for [issue #2](https://github.com/box1-org/box1-docs/issues/2).

The OpenShift AI dashboard, CPU workbench, dedicated NooBaa connection and
KServe model serving work on Box1. A notebook executed in the browser, wrote
and read S3 data, trained an Iris classifier, and received HTTP 200 with the
expected class `0` from the served model. Its saved notebook, marker and model
survived a full workbench Stop/Start through the dashboard.

## Access and configuration

- [Dashboard](https://rh-ai.apps.ocp.box1.org): sign in as `mike`, then open
  **Box1 AI test**. Workbench: `box1-workbench`; model: **Iris CPU smoke test**.
- Platform: OpenShift `5.0.0-rc.7`, Kubernetes `1.36.5`, single-node x86_64.
- OpenShift AI: `rhods-operator.3.4.2`, `stable-3.4`, catalog
  `redhat-operators-v422`, manual OLM upgrades.
- Enabled: dashboard, workbenches, KServe. Existing cert-manager `1.20.1`
  supplies certificates. Optional pipelines/training/registry/NIM are disabled.
- Workbench: Python 3.12 Data Science, 2 CPU / 4 GiB plus 100m / 64 MiB auth
  proxy; 10 GiB RWO PVC on `lvms-vg1`.
- Model: operator-provided MLServer `1.7.1`, CPU request 250m / 512 MiB,
  limit 1 CPU / 2 GiB. No GPU is requested; existing vLLM retains the RTX 5090.
- Storage: `box1-ai-test` ObjectBucketClaim on
  `openshift-storage.noobaa.io`, dedicated credentials in the same namespace.
  The runtime data connection is `noobaa-connection`; no credential values are
  stored in Git, the notebook, this document or the backlog.

The installation is **lab-only**. The user explicitly accepted the unsupported
version combination before installation. [Red Hat's 3.x configuration
matrix](https://access.redhat.com/articles/7137904) lists OpenShift through
4.22 for AI 3.4, and does not establish support for OpenShift 5.0.0-rc.7.
Successful tests do not establish vendor support. Resolution for supported use:
obtain written vendor confirmation or provision a separate supported cluster;
do not attempt an in-place downgrade of this cluster.

## Source and management

- [Initial manifests, notebook and runbook: 2297b82](https://github.com/box1-org/box1-gitops/commit/2297b82eeafd2cbec81b4e3a8470c7cfc9a3e09b)
- [Final Recreate strategy and quota: 63e4c9b](https://github.com/box1-org/box1-gitops/commit/63e4c9b)
- [Controller normalization: d6598c0](https://github.com/box1-org/box1-gitops/commit/d6598c0)
- [Approved scoped GitOps RBAC: 704a313](https://github.com/box1-org/box1-gitops/commit/704a313)
- [Operational runbook and cleanup instructions](https://github.com/box1-org/box1-gitops/blob/main/platform/openshift-ai/README.md)
- [Executed validation notebook](https://github.com/box1-org/box1-gitops/blob/main/platform/openshift-ai/validation/box1-ai-smoke.ipynb)
- [Connection provisioning script](https://github.com/box1-org/box1-gitops/blob/main/platform/openshift-ai/validation/provision-connection.py)

`box1-root` discovers three manual-sync Argo CD Applications:
`openshift-ai-operator`, `openshift-ai`, and `openshift-ai-test`. OLM manages the
operator; the operator manages shared platform components; Argo manages the
source configuration and test CRs. The credential-copy script creates the
connection outside Git. OBC provisioning manages its dedicated source credentials.

Argo initially lacked mutation rights for the new AI CRs and test resources.
The user explicitly approved scoped access for its application-controller
ServiceAccount: create/read AI singleton CR types, mutate only `default-dsc`
and `default-dsci`, and manage selected resource types only in `box1-ai-test`.
Those permissions have versioned manifests and are included in reconciliation.
No cluster-admin binding was added. Final verification showed all three AI
Applications and all existing Applications Synced/Healthy, with successful sync
operations. The test Application reconciled revision `63e4c9b`; the deployment
reported `strategy.type: Recreate`, quota limits.memory was `32Gi`, and the
InferenceService was Ready. A final post-reconciliation check read the existing
persistent marker and repeated inference successfully (HTTP 200, class 0).

## Evidence and limits

- Operator CSV Succeeded; DSCInitialization, dashboard, workbenches and KServe
  reported Ready. The dashboard showed the test project, running workbench and
  Ready model. The browser user menu showed `mike`.
- Notebook S3 put/get matched the original bytes with TLS verification enabled.
  A head request to unrelated `first.bucket` returned HTTP 403 using the same
  credentials, demonstrating that they do not grant access to that bucket.
- The workbench saved `box1-ai-smoke.ipynb`, a 41-byte marker and a 975-byte model.
  Stop/Start recreated its pod; a separate cell read the existing files before
  rerunning the cell that writes them.
- KServe downloaded `model-settings.json` and `model.joblib` from the dedicated
  S3 bucket. The browser notebook POSTed `[5.1,3.5,1.4,0.2]` to
  `/v2/models/iris/infer`; response was HTTP 200, model version `1`, output `[0]`.
- Anonymous dashboard and notebook HTTP requests redirected to login (302).
  Public HTTPS validation succeeded without disabling certificate verification.
- The model endpoint is internal HTTP only; no public model Route was created.
  It does not implement model-level authentication or a namespace NetworkPolicy.
  Add appropriate access controls before sensitive or public model use.
- One observed idle sample: workbench 16m CPU / 615 MiB, model 2m / 407 MiB.
  Node sample before installation: 1136m / 63810 MiB; after testing:
  3137m / 71566 MiB. These are samples, not a controlled benchmark.
- The default model download initializer has a 24 GiB limit but only a 100 MiB
  memory request. Initial admission failed against a 16 GiB namespace limit
  quota. Final quota permits 32 GiB of limits, retaining 10 GiB memory requests,
  4 CPU requests, 8 CPU limits, zero GPU and 30 GiB storage. The user requested
  `deploymentStrategy: Recreate`; model updates briefly interrupt inference,
  and the quota needs to accommodate only one 24 GiB initializer ceiling plus
  the workbench. Per-container requests and limits remain unchanged.
- Existing Argo applications stayed Healthy; cluster operators were all
  Available and not Degraded. Representative existing vLLM, Developer Hub,
  Keycloak, NooBaa and service deployments retained their desired availability.

Full uninstall/reinstall, disaster recovery, load testing, GPU integration and
vendor support for this prerelease platform were not tested or established.
Routine workbench restart and data persistence were tested.

## Recovery and follow-ups

Follow the source runbook for ordered bootstrap, credential provisioning,
notebook reproduction and cleanup. Workbench PVC and bucket StorageClasses use
Delete reclaim policies. Back up and verify data before approving removal of
those resources. Full cleanup/recovery instructions are untested; do not delete
shared cert-manager, LVMS, NooBaa or GPU operators.

The unresolved platform support limitation remains explicit. For future use,
recheck the compatibility matrix and confirm operator channel plans before
upgrades. The NooBaa console signing workaround remains a separate concern
tracked in [issue #1](https://github.com/box1-org/box1-docs/issues/1); direct S3
notebook access did not require changing that workaround.
