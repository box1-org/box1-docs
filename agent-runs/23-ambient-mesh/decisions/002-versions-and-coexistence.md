# 002 Operator versions and coexistence with the Gateway API istiod — proposed

**Versions:**
- `servicemeshoperator3`, channel `stable-3.5` (v3.5.0), `installPlanApproval: Manual`. The minor-version channel avoids silent minor jumps.
- `kiali-ossm`, channel `stable` (v2.33.1), Manual.
- Both AllNamespaces in `openshift-operators`, following the Tempo/OTel pattern in `platform/observability/operators/`.
- After install, read the Istio versions the 3.5 CSV supports, and set `Istio.spec.version` and `ZTunnel/IstioCNI.spec.version` to the newest of them.
- Kiali/OSSM compatibility for 3.5 is **not established**; check the installed CSVs before creating the Kiali CR.

**Layout:**
- `Istio` named `default` in `istio-system`, `profile: ambient`, `updateStrategy: InPlace`, so the revision is `default`. The ingress controller's revision is `openshift-gateway`.
- `IstioCNI` named `default` in `istio-cni`.
- `ZTunnel` named `default` in `ztunnel`.
- `pilot.trustedZtunnelNamespace: ztunnel`.
- `meshConfig.discoverySelectors: [{matchLabels: {istio-discovery: enabled}}]`. Label `istio-system`, `ztunnel` and the seven service namespaces; never `openshift-ingress`.

**Coexistence evidence (read-only):**
- The gateway istiod writes its root CA to `openshift-gw-ca-root-cert`, not `istio-ca-root-cert`.
- It does not run the GatewayClass controller.
- It trusts only `kube-system/ztunnel`.
- Its waypoint class would differ from `istio-waypoint`.

**Open risk (stop condition):**
- The `*.istio.io` CRDs are owned by the ingress operator. OLM installing the OSSM CSV will try to take them over.
- It is not established whether the ingress operator then yields or reconciles them back.
- Plan: with Manual approval, inspect the InstallPlan's CRD steps before approving.
- After install, check that `istiod-openshift-gateway` stays healthy and `data-science-gateway-class` stays Accepted, and that the CRD labels and ownership have settled.
- If the two operators fight over the CRDs, stop and roll back by deleting the Subscription and CSV. Deleting the CSV does not remove CRDs.
