# 02 Local tests

Environment: macOS, node v25.2.1, npm 11.6.2; box1-templates fresh clone.

## Baseline on main 5663eb3 (before any change)
`npm ci && npm run validate && npm run test:onboarding && npm run test:onboarding-oci` exit 0. test:onboarding 57/57, test:onboarding-oci 26/26.

## Characterisation commit b0e65d8 (old plugin code + new test)
Same command, exit 0. test:onboarding 58/58 (57 + characterisation), test:onboarding-oci 26/26. Fixture generated with UPDATE_CHARACTERISATION=1 on this code; three further runs without the switch passed (deterministic). validate output is deterministic (sha1 of all 257 rendered files identical across two runs).

Mutation check on b0e65d8 (each applied alone, then reverted): service marker key order swapped; 'initial VirtualMachine' message changed; build task 'box1-quarkus-maven' renamed; service templateVersion 1.1.0->1.1.1. Each made the characterisation test fail (fail 1).

## After refactor ca3bf00
Characterisation test passes with the test and fixture unchanged. Exactly three tests failed before rewrite, all the coupled ones the prompt names (w.vm/deepEqual PROFILES.service; w.vmPlatformChecks; enum regex). After rewrite: 58/58.

## Final head d8e8533
`git diff b0e65d8 d8e8533 -- scripts/test-onboarding-characterisation.cjs scripts/fixtures/` is empty.

```
PASS orders-api: render, ownership, pipeline contract, namespaces, Kustomize
PASS inventory-service: render, ownership, pipeline contract, namespaces, Kustomize
PASS quarkus-golden-path-smoke: render, ownership, pipeline contract, namespaces, Kustomize
PASS aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: render, ownership, pipeline contract, namespaces, Kustomize
PASS github-repository team-notes: render, ownership, no build or deployment files
PASS github-repository box1-example-docs: render, ownership, no build or deployment files
PASS github-repository aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: render, ownership, no build or deployment files
PASS github-repository rejected unsafe names
PASS rejected unsafe/reserved names
PASS rhel-image-vm vm-golden-check: render, plugin bundle check, Kustomize, Containerfile, pipeline contract, catalog
PASS rhel-image-vm erp-appliance: render, plugin bundle check, Kustomize, Containerfile, pipeline contract, catalog
PASS rhel-image-vm vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv: render, plugin bundle check, Kustomize, Containerfile, pipeline contract, catalog
PASS rhel-image-vm rejected unsafe keys, packages, names and sizes
✔ service and virtual-machine profiles behave exactly as recorded before the dispatch refactor (132.067083ms)
✔ an unknown profile is rejected before any work (1.44725ms)
✔ a profile that differs from the stored record is rejected by every phase that checks it (0.921916ms)
✔ service: resume after PLATFORM_READY and IMAGE_BUILT repeats no platform or build work (0.45125ms)
✔ service: a catalog step without a profile input completes from the stored record (1.765291ms)
✔ virtual-machine: resume after PLATFORM_READY and IMAGE_BUILT repeats no platform or build work (0.104ms)
✔ virtual-machine: a catalog step without a profile input completes from the stored record (0.166292ms)
✔ a test-only profile is one table entry: it joins the action enum and supplies its record and marker fields (3.103125ms)
✔ a profile without a GitOps workload skips provision and promotion, and its catalog predicate needs no deploymentImage (0.846833ms)
✔ a profile without a source repository or build creates its record in provision and adopts its digests (0.442291ms)
✔ a profile with no build at all never starts one (0.130417ms)
✔ every table entry declares the whole handler contract (0.072917ms)
✔ service: a fresh platform phase requests the Application sync, then waits for build prerequisites (1.4455ms)
✔ service: the build phase awaits the requested Application sync before platform readiness (1.643708ms)
✔ service: rejected build results fail before the credential Secret is deleted (0.589583ms)
✔ virtual-machine: a fresh platform phase requests the Application sync, then waits for build prerequisites (0.114208ms)
✔ virtual-machine: the build phase awaits the requested Application sync before platform readiness (0.1155ms)
✔ virtual-machine: rejected build results fail before the credential Secret is deleted (0.757667ms)
✔ profiles: service stays the default with its original record values (1.32525ms)
✔ a phase must run with the profile recorded for the onboarding (0.785667ms)
✔ the rendered template bundle passes the VM bundle check, and not the service one (17.170208ms)
✔ VM bundle check rejects unsafe or off-contract changes (26.177583ms)
✔ VM repository marker records the profile; service marker keeps its original shape (1.592584ms)
✔ VM build barrier waits for the bootc release identity and privileged binding (0.2045ms)
✔ VM platform readiness checks the updater, Group pull binding and VirtualMachine instead of a Deployment (0.240792ms)
✔ VM first build runs bootc build, disk and channel as ci-bootc-release and keeps the disk digest (0.48575ms)
✔ VM first build refuses a run without a disk digest (0.106458ms)
✔ VM first promotion pins the disk, lists the DataVolume and starts the VM, and nothing else (3.136833ms)
✔ VM verify waits for disk import, boot and guest agent, and fails at once on a failed import (0.387667ms)
✔ the VM template runs the same delivery phases with the virtual-machine profile (2.595375ms)
✔ PostgreSQL NetworkPolicy is accepted only when scoped to this service (36.476416ms)
✔ development-only merge policy rejects namespace, RBAC and baseline changes (9.183792ms)
✔ phase resume reuses completed provision, platform, build, and promotion work (0.521459ms)
✔ restart after onboarding PR creation validates and resumes the existing PR (0.155333ms)
✔ a concurrent task cannot acquire an unexpired service lease (0.701625ms)
✔ readiness gates do not advance while namespace or permissions are missing (0.613792ms)
✔ readiness aggregation retains diagnostics when a condition fails (0.177417ms)
✔ readiness cancellation stops before another observation (0.19275ms)
✔ build barrier ignores unrelated platform readiness conditions (0.158417ms)
✔ Argo sync PATCH uses Kubernetes merge-patch content type (1.750417ms)
✔ new service explicitly syncs the workload index and service Application (1.426792ms)
✔ existing healthy service Application skips a duplicate sync request (0.179333ms)
✔ persist Secret before creating initial CI, and resume the same completed run (0.422833ms)
✔ failed initial build cleans its owned credential Secret (0.124791ms)
✔ failed required checks never produce a merge; retry uses an identical tree (0.198042ms)
✔ checks from another App cannot authorize the merge (0.097959ms)
✔ fresh validation retries keep the exact GitOps tree and merge only the new checked SHA (0.129791ms)
✔ Lease renewTime uses Kubernetes MicroTime precision (0.059542ms)
✔ catalog replay reuses the owned entity without adding another location (0.094834ms)
✔ a pending duplicate catalog location is resolved without swallowing other errors (0.076709ms)
✔ catalog registration refuses an entity from another repository (0.038875ms)
✔ catalog submit records the location without waiting for entity processing (0.102416ms)
✔ catalog failures keep provisioning incomplete and produce durable failure state (0.164542ms)
✔ new onboarding writes only to development workload repository (0.114584ms)
✔ ConfigMap state conflicts are surfaced without overwriting newer state (0.174083ms)
✔ wait persists an explicit waiting phase status (0.052917ms)
✔ parallel waits serialize state writes against a resourceVersion-enforcing API (3.752042ms)
✔ a waiting save during a build does not move the phase back (4.908875ms)
✔ a real state conflict from another process still surfaces after serialization (2.622417ms)
✔ concurrent waits share one Lease renewal (4.892458ms)
✔ an out-of-sync Application with no active operation gets an explicit sync request (0.132833ms)
✔ a sync request waits for an active Argo operation and refuses a failed one (0.144416ms)
✔ platform stops at the build boundary and a restart does not repeat the sync request (0.143791ms)
✔ awaitServiceSync honours the persisted request time after a restart (0.097042ms)
✔ the build overlaps platform readiness, which is recorded once both finish (5.1305ms)
✔ a build failure stops platform observers and reports the build error (5.245375ms)
✔ a platform failure lets the build finish, keeps its digest, and a retry does not rebuild (5.902875ms)
✔ promotion refuses to start before platform readiness completes (0.097ms)
✔ the compatibility wrapper runs exactly the template phases in order (3.093708ms)
✔ the wrapper completes against a resourceVersion-enforcing API with real state and Lease writes (32.819625ms)
✔ promotion requests a sync when Argo still reports Synced at the previous revision (0.176083ms)
✔ promotion requests its sync after the PR merges, and a retry does not repeat it (0.21725ms)
✔ a restart between the promotion merge and the sync request still requests the sync (0.056584ms)
✔ promotion records an Application already at the merged revision without a sync request (0.052292ms)
✔ verify fails at once when the requested promotion sync fails, but ignores an older failure (0.248041ms)
ℹ tests 75
ℹ pass 75
ℹ fail 0
✔ a valid artifact passes and reports its identity (19.98775ms)
✔ rejects a revision that is not the one built (7.46025ms)
✔ rejects a missing dynamic-packages annotation (7.498667ms)
✔ rejects more than one layer (6.396833ms)
✔ rejects the wrong platform (6.156875ms)
✔ rejects a missing source label (6.497583ms)
✔ rejects a missing plugin file (8.751167ms)
✔ rejects a renamed package (14.69475ms)
✔ rejects a lost action (15.314459ms)
✔ rejects a private dependency (13.150708ms)
✔ rejects a malformed digest (0.119167ms)
✔ rejects registry bytes that do not hash to the requested digest (16.944833ms)
✔ rejects an artifact the registry cannot serve (0.143875ms)
✔ authenticates with a pull-scoped token and verifies registry content (15.486542ms)
✔ the pinned CLI matches the deployed RHDH compatibility target (0.280916ms)
✔ a release updates only the digest reference and rollout annotation (0.373833ms)
✔ a release rejects a missing source revision annotation (0.061708ms)
✔ a release rejects a malformed release digest (0.022208ms)
✔ a release rejects a mutable tag in the current configuration (0.027209ms)
✔ a release rejects a wrong plugin path (0.021625ms)
✔ a release rejects duplicate plugin definitions (0.030834ms)
✔ a release rejects no plugin definition (0.022334ms)
✔ a release rejects a stale rollout annotation (0.033125ms)
✔ a release rejects a missing rollout annotation (0.0245ms)
✔ the GitOps PR records everything needed to review and roll back (0.063834ms)
✔ nothing in the release path deploys or publishes to npm (0.374208ms)
ℹ tests 26
ℹ pass 26
ℹ fail 0
```

Plugin load smoke: `node scripts/smoke-onboarding-plugin.cjs plugins/box1-onboarding plugins/box1-onboarding/oci-package.json` -> `Loaded box1-scaffolder-onboarding-dynamic 1.3.0: 10 actions registered`

scripts/test-onboarding-sync-equivalence.cjs was also run against a worktree of main 5663eb3 (old plugin code): pass 6, fail 0.

Not run locally: `npm run package:onboarding-oci` (needs tools/rhdh-cli install and a container tool); the PR pipeline box1-onboarding-plugin-pr runs it.
