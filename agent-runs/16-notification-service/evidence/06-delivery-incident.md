# Phase 6 delivery: first deployment error (2026-11-06 EST)

The user merged all five PRs. Merge times (UTC):

| PR | Merged | Merge commit |
|---|---|---|
| notification-service#1 | 17:52:44Z | `bacc353` |
| box1-ops-contracts#9 | 17:54:15Z | `4748ff5` |
| box1-gitops#75 | 17:55:55Z | `01cc506` |
| box1-gitops#76 | 17:56:47Z | `ad5edd6` |
| box1-workloads-dev#94 | 17:59:21Z | `ed5afc3` |

The service merged **before** the workloads change, which is the ordering risk in release review H1 and D-014.

- **Release.** PipelineRun `box1-ci/notification-service-release-mpbtb` on `bacc353`:
  - build Succeeded, with image `sha256:69788422d2f3beef94a255e4247ba3142f662f9edb25018489f2058edd5b363a`;
  - security Succeeded;
  - promote merged box1-workloads-dev#108 (`1d54764`), then failed (`StepFailed`) waiting for Argo health;
  - smoke did not run.
- **Symptom.** Argo synced `1d54764`: the new image with no env. The pod crash-looped with "Failed to load config value of type class java.time.Instant for: notification.consumer.events-floor". The template pod kept serving (`maxUnavailable: 0`). Argo reported Degraded (progress deadline exceeded).
- **Resolution of that error.** At 18:02 UTC Argo auto-synced `ed5afc3` (#94). The Deployment now has `NOTIFY_EVENTS_FLOOR` and the datasource env. The app and PostgreSQL pods are in `CreateContainerConfigError`, waiting for Secret `notification-service-postgres`, which does not exist yet (existence checked by name only). The template pod still serves.
- **Still missing on the cluster:**
  - The KafkaTopic `box1.notification.dlq.v1`. #75 merged, but `box1-kafka` syncs manually, and it is the only OutOfSync resource there. The new image refuses to start without the topic when Kafka is reachable.
  - My selective sync (Application `operation`, one resource, prune off, revision `ad5edd6`) was **denied by the session's permission classifier**. It was not attempted another way.
- **Keycloak.** The `notification-service` KeycloakClient is `ready=true`. Its roles have not been checked yet.
- **Floor.** box1-workloads-dev#110 (not merged) moves `NOTIFY_EVENTS_FLOOR` to `2026-11-06T18:03:00Z`. This is open decision O-8; the floor must be settled before first start.
- **contracts.ref.** It still pins `1078fd4`, the PR #9 head. #9 merged as `4748ff5`, so a repin is pending.

## Resolution (user approvals 2026-11-06 13:1x EST)

- **Floor.** The user said "just merge it". box1-workloads-dev#110 was merged as `2c8f93c`; the floor is now `2026-11-06T18:03:00Z`.
- **DLQ topic.** The user said "sync it". A selective sync of `box1-kafka` ran via the Application `operation` field: one resource, `KafkaTopic box1.notification.dlq.v1`, revision `ad5edd6`, prune false. Result: `Succeeded`. The topic is Ready with 3 partitions and `retention.ms=1209600000`, and `box1-kafka` is fully Synced.
- **Secret.** The user created it ("done"). I checked only that it exists, by name.
