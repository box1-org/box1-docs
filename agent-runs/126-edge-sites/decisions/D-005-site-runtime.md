# D-005 Site runtime: persistence, images, identity, health

- **Persistent data on `/var`** (`/var/lib/box1-site/{postgres,broker,secrets}`), kept across reboot, `bootc upgrade`
  and rollback. No separate data disk: the merged `vm-instance` bundle (#138) has none. A VM rebuild from its
  instance loses buffered data (runbook).
- **Quadlet images mirrored into `box1-ci` by digest** (box1-workloads-dev#225): AMQ Broker 7.14.1
  (`amq7/amq-broker-rhel9@sha256:e77cb86f…`) and PostgreSQL 16 (`rhel10/postgresql-16@sha256:640273e1…`), pulled with
  the guest's existing registry token (`/run/ostree/auth.json`, `system:image-puller` on `box1-ci`); the image holds
  no registry credential.
- **Broker**: instance created on first start with only the MQTT acceptor, NIO journal, no web console, anonymous on
  loopback only. Every image build starts the pinned image with the same script and requires MQTT on 1883.
- **Services** run as `box1-site` (#140), `ConditionPathExists=/etc/box1/site.env`, so a VM without site identity
  (the source VM `site-gateway-os`) runs none of them and its greenboot checks pass.
- **Database password** generated once at first boot (root-only env files read by systemd), never in Git or the image.
- **greenboot** (0.16.3) required checks: PostgreSQL, MQTT listener, site-gateway ready (database + migrations + MQTT,
  never Kafka), site-ops; bounded waits. `greenboot-default-health-checks` is **not** installed: its repository DNS
  check would roll back a site that reboots while disconnected.
- **Collector**: RHEL 10 `opentelemetry-collector` 0.158.0 exists, installed without scriptlets in its own layer
  (its SELinux module commit broke the image's later `setsebool -P` on cluster buildah, observed in PR build
  `site-gateway-os-validate-nnkxq`), run by `site-otel-collector.service` (DynamicUser, `systemd-journal`).
