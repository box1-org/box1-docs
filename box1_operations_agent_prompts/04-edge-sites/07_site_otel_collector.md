# Edge sites 07 — In-guest OpenTelemetry collector for site traces, logs and metrics

> **Observability work in the site image and `box1-gitops` observability.** Site traces, journald logs and host metrics reach the existing Box1 observability stack. Read `../00-shared/00_AGENT_CONTRACT.md`, `02_REPO_AND_GITOPS_CONVENTIONS.md`, `03_QUALITY_GATES.md` and `06_RESOURCE_AND_SECURITY_BOUNDARIES.md`. A `frontier` run also reads `07_FRONTIER_EXECUTION_PROFILE.md`.

**Safety**
- Changes to the shared collector, ClusterLogForwarder, LokiStack or monitoring are shared infrastructure: approved GitOps PRs only.
- Detaching a site NIC is a fault injection: approval needed, site VMs only.
- Logs must contain no credentials. The user merges, about 10 seconds apart ([#64](https://github.com/box1-org/box1-docs/issues/64)).
- Do not use Chrome.

**Issue:** [box1-docs#132](https://github.com/box1-org/box1-docs/issues/132), a sub-issue of [#126](https://github.com/box1-org/box1-docs/issues/126).

**Dependencies**
- `01_site_foundation.md`: the site image and units.
- `02_site_forwarder_outbox.md` and `05_asset_site_ingestion_stale_alert.md`: the reading path whose trace must be end to end, and the buffer-depth metric.
- [#138](https://github.com/box1-org/box1-docs/issues/138): the site instances.

## Mission

Export the Quarkus site apps' traces to `box1-collector`, so a trace runs from a site reading across Kafka to asset-service and its alert. Run an OpenTelemetry collector in each guest that reads journald and host metrics and exports them, so site logs are queryable in Observe → Logs and host metrics in Prometheus.

## Verified baseline (observed 2026-11-09; verify before relying)

`box1-gitops` main `4bcc907`.

- **Collector:** `OpenTelemetryCollector` `box1` (`platform/observability/tracing/collector.yaml`), OTLP gRPC `:4317` and HTTP `:4318` (L35–41), **no authentication and no TLS**. Its **only pipeline is traces** (L66–72), exporting to the Tempo gateway (L48–65). Service `box1-collector.box1-observability.svc`.
- Its NetworkPolicy (`tracing/networkpolicy.yaml` L59–89) admits 4317/4318 from any namespace. Reachability from a VM is **not verified**.
- **Logs:** Vector `ClusterLogForwarder` `box1` (`logging/collector.yaml` L41–96) collects only seven listed service namespaces (L52–63) into LokiStack `logging-loki`. VM namespaces and guest journald are not collected. **There is no OTLP log path into Loki.**
- **Metrics:** user-workload monitoring is enabled; services expose `/q/metrics` scraped by ServiceMonitors. **There is no OTLP metrics path into Prometheus.**
- **Package:** no repository installs an `opentelemetry-collector` RPM; availability on RHEL 10 is **not verified** (#126 lists it as a risk).
- The site VMs are outside the ambient mesh, like `legacy-erp`.

## Decided design

From the issue and #126's decisions.

- Site apps use Quarkus OpenTelemetry, exporting OTLP traces to `box1-collector`, with W3C context propagated through MQTT (where the simulator starts the trace) and Kafka headers.
- An in-guest collector reads journald (site apps, AMQ Broker, PostgreSQL, greenboot, bootc) and host metrics (CPU, memory, disk, filesystem), adds `siteId` as a resource attribute, and exports OTLP to `box1-collector`.
- **Package first.** Use the RHEL 10 `opentelemetry-collector` RPM if it exists in the entitled repositories; otherwise run the Red Hat build of the collector as a digest-pinned quadlet. Record which.
- **Logs path (decide):** add a logs pipeline to `box1-collector` that exports to LokiStack through its OTLP endpoint (if the installed Logging version supports it), or another approved path. Logs must be queryable by `siteId` and `traceId` under the existing tenancy.
- **Metrics path (decide, as the issue requires):** for example, a Prometheus exporter on `box1-collector` scraped by a ServiceMonitor, or remote write to user-workload monitoring. Include `02`'s buffer-depth metric.
- **Disconnected behaviour:** a bounded in-guest queue (memory or file storage with a size limit) and a documented drop policy.
- Log lines carry `siteId` and `traceId`; credentials are filtered.

## Scope and guardrails

**In scope:** the site image's collector, its config and unit; Quarkus OTel configuration in `site-gateway`; the `box1-collector` logs and metrics pipelines and any ServiceMonitor; documentation.

**Out of scope:** changing service namespaces' existing log forwarding; mesh enrollment of the sites.

## Verifiable acceptance evidence

These items come from the issue. Tick each one on #132 only with the evidence named.

- [ ] One site-originated reading's trace is visible in Observe → Traces, from site-gateway to asset-service.
  - Evidence: the trace ID, its span list (simulator or gateway, Kafka, asset-service), and the reading it carried.
- [ ] Site app and OS logs are queryable in Observe → Logs by `siteId` and by `traceId`.
  - Evidence: the LogQL queries and results for each, covering a site app line and an OS line (for example bootc or greenboot).
- [ ] Host metrics (CPU, memory, disk) and the buffer-depth metric for both VMs are queryable.
  - Evidence: the PromQL queries and results for both sites.
- [ ] While a site is disconnected, the collector's behaviour is documented and bounded (what it drops or buffers).
  - Evidence: the configured limits, an approved NIC detach, the queue size during it, and what arrived after reconnection.

## Frontier profile

Use with `../00-shared/07_FRONTIER_EXECUTION_PROFILE.md`.

**Run state:** `box1-docs/agent-runs/132-site-otel/`.

**Discovery must cover**
- RPM availability in the entitled RHEL 10 repositories, and the Red Hat collector image otherwise.
- The installed Logging and LokiStack versions and their OTLP support and tenancy.
- Guest reachability of `box1-collector`.
- How Quarkus propagates context through Camel MQTT and Kafka.

**Design decisions to record**
- Collector packaging; logs path; metrics path; queue limits; resource attributes and label cardinality; journald units collected.

**Phase exit additions**

| Phase | Must also show |
|---|---|
| 0 Discovery | Package availability and OTLP log support confirmed, not assumed |
| 6 Delivery | `box1-collector` changes reconciled; site OS digest carrying the collector on both sites |
| 7 Live acceptance | All four criteria |

**Verification scenarios**
- `box1-collector` restarted; a site disconnected beyond the queue limit; a log line containing a secret-like string is redacted; collector memory under load stays within its limit.

**Stop conditions**
- No supported collector package or image.
- No approved logs or metrics path into the existing stack.

## Final handoff

Use `../00-shared/05_HANDOFF_TEMPLATE.md` with the run state block. List the packaging, pipelines, queries, limits, digests, evidence, and rollback (revert the `box1-collector` PR; promote the previous site digest).

Tick the completed items on #132.
