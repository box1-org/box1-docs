# Operations pass

Fresh read-only subagent, given the diffs, prompt and profile plus read access to the GitOps clones; not the implementation reasoning. 2026-11-05 ~19:34 EST.

OPS-1 (high) Runbook replay cannot work: scaling to 0 is reverted by Argo selfHeal and kafka-consumer-groups refuses to reset an active group; no exec location; --to-datetime is local time.
OPS-2 (medium) The consumer re-applies the 24 h age check; topic keeps 48 h, so replays of 24-48 h windows and any catch-up after a >24 h outage are dead-lettered as POLICY_STALE_TIMESTAMP. Runbook calls replays harmless and DLQ re-copy idempotent.
OPS-3 (medium) Shutdown during a database retry rethrows; SmallRye nacks; the valid reading is dead-lettered. Same as ARCH-5.
OPS-4 (medium) During a database outage readiness goes DOWN, the Route drops the pod, the console and stop-all return 503, heartbeats only log, the reaper cannot run: a run keeps emitting up to its duration (15 min). Fail safe: cancel local runs once heartbeats fail longer than staleHeartbeat.
OPS-5 (medium) Outbox batch of 100 rows with 15 s per-row waits can take ~25 min during a broker outage, blocking new alert events; claim lapses after ~4 rows. Same family as PERS-6.
OPS-6 (medium) First deploy and release smoke depend on manual order; "harmless" wording is wrong (Deployment goes Progressing=False, Argo Degraded, promotions fail smoke). Add a preflight to the runbook.
OPS-7 (medium) Flyway at start crash-loops while PostgreSQL is not ready after a node reboot. Set connect retries within the startup-probe budget.
OPS-8 (low) Stale-assets gauge permanent (asset_last_seen never pruned). Same as PERS-5/ARCH-8.
OPS-9 (low) Retention below ingest ceiling; count(*) per minute. Same as PERS-4.
OPS-10 (low) Readiness can time out under pool pressure (2 s probe, 5 s acquisition); asset_outbox_pending queried on every scrape.
OPS-11 (low) Memory request 256Mi close to measured 213-232 MiB RSS; catch-up throughput not measured.
OPS-12 (low) KAFKA_BOOTSTRAP_SERVERS defaults to localhost in prod; offset `latest` (as ARCH-4); load runs ungated (as ARCH-13).
OPS-13 (info) Docs: rhel9 PostgreSQL image re-applies POSTGRESQL_PASSWORD at start (rotation note wrong); no DLQ re-copy command; no backup procedure; MDC trace IDs on run threads not verified.
OPS-14 (info) Rollout: stop-all on the new pod resumes only its producer; per-pod readouts; no preStop; gate now blocks on scanner/policy failure.

Verified OK (reviewer): smoke paths public and box1_greetings_total present; probes; restart safety; rollout concurrency (Flyway lock, SKIP LOCKED); PVC sizing estimate ~0.6-1 GiB at 2M rows; resource fit; lag metric; doc metric names; DLQ topic conventions; PostgreSQL NetworkPolicy.

## Outcomes (asset-service 7cdc138, workloads bb0bcae)

| Finding | Outcome |
|---|---|
| OPS-1 | Fixed. Replay through a Git env toggle, `oc exec` in the broker pod, `--by-duration`. Not exercised. |
| OPS-2 | Fixed (see ARCH-4); runbook corrected. |
| OPS-3 | Fixed (see ARCH-5). |
| OPS-4 | Fixed. Local runs stop after heartbeats fail for 20 s. Scenario `dboutage`. |
| OPS-5 | Fixed (see PERS-6). |
| OPS-6 | Fixed. Runbook preflight and corrected wording; manifest comment corrected. |
| OPS-7 | Fixed. Flyway connect retries 20 x 5 s. |
| OPS-8 | Fixed (see ARCH-8). |
| OPS-9 | Fixed (see PERS-4). |
| OPS-10 | Fixed. Acquisition timeout 2 s; outbox gauge measured on a schedule. |
| OPS-11 | Fixed in part: request 320Mi. Catch-up RSS not measured. |
| OPS-12 | Fixed. No Kafka bootstrap default in prod; earliest; control default off. |
| OPS-13 | Fixed. Rotation, DLQ re-copy, backup documented. MDC trace IDs on run threads still not verified. |
| OPS-14 | Recorded. Per-pod readouts and pause during rollout are bounded; preStop inherited from the template. |
