# RHDH onboarding durable workflow

The Box1 onboarding plugin now exposes `provision`, `platform`, `build`, `promote`, and `verify` phases, while `onboard` remains a compatibility wrapper. The onboarding ConfigMap is the durable record (`schemaVersion: 2`) and the per-service Lease prevents concurrent attempts.

Each phase records its status, transition time, attempt history, external identifiers, and the last error. Retries reuse recorded repositories, pull requests, PipelineRuns, digests, and catalog locations. Kubernetes resource-version updates protect the ConfigMap from stale writers. Platform observations run with bounded concurrent checks and retain condition diagnostics. Temporary build credentials are labelled, owner-linked to the PipelineRun, and removed after success or failure.

Catalog submission and verification are separate actions. Submission records the source location without waiting for catalog processing; verification can be retried independently. The canonical plugin is packaged into the GitOps Developer Hub transport with `npm run package:onboarding`; CI runs `npm run check:onboarding-package` to detect drift.

No timing improvement is claimed yet. Collect comparable onboarding runs before changing the dependency barrier or reporting p50/p95 gains.
