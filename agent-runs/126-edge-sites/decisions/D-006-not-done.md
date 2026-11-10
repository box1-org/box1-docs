# D-006 Deliberately not done in this run

- **Egress NetworkPolicy** (#126 work item): not written. The sites reach asset-service and Keycloak through public
  Routes (router on the host network), Kafka, the registry and box1-collector through Services; a policy that is
  wrong would cut a site off. Enforcement for a VM on the pod network is also unverified. Needs a live test window.
- **Per-site Kafka identity** (#131 Kafka half): blocked on #71.
- **Staged rollout mechanism** (#141): separate issue; #133's checks and the facts it reads are in place.
- **agentic-operations site tool**: not added (needs approval per 09 prompt); follow-up.
- **Live acceptance**: nothing in #127–#133 is live-verified; every merge outside site-gateway is the owner's.
