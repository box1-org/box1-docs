# RHDH onboarding refactor — 2026-11-04

## Outcome

The Box1 RHDH onboarding implementation has durable phase boundaries and resumable state while preserving the two GitOps PRs, immutable digest promotion, explicit Argo synchronization, exact-head validation, ownership markers, Lease coordination, and temporary credential cleanup.

## Delivered

- Registered `box1:development:provision`, `platform`, `build`, `promote`, and `verify`, with `onboard` retained as the compatibility wrapper.
- Added nonblocking `box1:catalog:submit` and independently retryable `box1:catalog:verify`.
- Added schema-versioned ConfigMap state, optimistic resource-version updates, phase status transitions, structured wait logs, and cancellation recording.
- Added concurrent bounded readiness checks with condition diagnostics.
- Added canonical-versus-packaged plugin drift checking and packaging checksum enforcement.
- Added restart, Lease, readiness, build, GitOps, catalog, template, and state-conflict coverage.

Validation on 2026-11-04: `npm run validate`, `npm run test:onboarding` (26 passing), `npm run check:onboarding-package`.

No performance improvement is claimed; representative onboarding timing data remains a follow-up.
