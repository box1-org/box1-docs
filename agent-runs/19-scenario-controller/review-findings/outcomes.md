# Reviewer findings and outcomes (Phase 5)

Five passes ran as fresh read-only subagents, given the diffs (scenario-controller `203968e..e061f6d`, inventory-service
`094772a..fca04be`), the prompt and the contracts, not the implementation reasoning. They are same-model reviews and do
not replace human PR review or CI. The Release pass waits for a deployment (Phase 6). Reports: `architecture.md`,
`persistence.md`, `messaging.md`, `security.md`, `operations.md`.

57 findings in total: 0 high, 13 medium or medium-low. Repairs are in scenario-controller `7f0f9ea` and
box1-workloads-dev#103 `4c039d3`. Afterwards the full suite was rerun (48 tests + 5 IT, Checkstyle 0, SpotBugs 0), and so
was the local end-to-end run (`evidence/07-local-e2e-after-review.txt`).

| Finding | Severity | Outcome |
|---|---|---|
| ARCH-1 / OPS-1 / PERS-5: a rolling update lets a new pod abort the old pod's live run | Medium | **Fixed.** `strategy: Recreate` (workloads#103); documented single replica |
| ARCH-2: halt interrupts the shared worker thread and can hit a new run | Medium | **Fixed.** Per-run Future cancel; compare-and-set handle |
| ARCH-3 / MSG-2: the crash run verifies without a crash | Medium | **Fixed.** Operator confirmations `crash-armed` (before the order) and `crash-observed`, audited; NOT_VERIFIED without them. Test added |
| ARCH-4: ERP faults and holds have no ERP-side expiry | Medium | **Recorded** as an acceptance limitation (runbook, architecture). An ERP-side TTL is another service's change: follow-up for the user |
| MSG-1: "shipped exactly once" could never fail | Medium | **Fixed.** Settle window, then one `shipment.confirmed.v1` by event ID and a stable adapter shipment ID. Test with a duplicate |
| MSG-3 / PERS-6: over-restock makes the tribble scenario fail forever | Medium | **Fixed.** Contention orders all available stock; reset waits for the run's orders to be decided. Test with two available |
| MSG-4: a REJECTED request passes as released | Medium | **Fixed.** Release must be PENDING or SHIPPED. Test added |
| PERS-1 / ARCH-6: ending a run is not atomic or recoverable | Medium | **Fixed.** End and RESULT in one transaction; unrecorded resets completed at startup and by the sweep. Test added |
| SEC-1 / ARCH-8: the gate checks where the controller runs, not where it writes | Medium | **Fixed.** Upstream host allowlist (gate 3); targets in the START audit. Test added |
| PERS-2: a failed start leaves an orphan open run | Medium-low | **Fixed.** Run, START audit and impact in one transaction |
| PERS-3 / OPS-6 / ARCH-11: retention below 90 days fails silently | Medium-low | **Fixed.** Retention is fixed at 90 days by database time; setting removed. Test added |
| OPS-2 / ARCH-5: an interrupted call records FAILED and drops the guided reset | Medium | **Fixed.** Any exception after a stop is a stop |
| OPS-3 / ARCH-7: a scenario missing from the catalog blocks startup | Medium-low | **Fixed.** Such runs end RESET_FAILED; recovery catches all runtime errors |
| MSG-5: the held signal is not tied to this hold | Medium-low | **Fixed.** Baseline before the hold; must rise; NOT_VERIFIED otherwise |
| MSG-6: the delay measured downstream lag | Low | **Fixed.** The adapter's `acknowledgedAt` to `statusAt` |
| MSG-7: no retry; failed creates leave orders unrecorded | Low | **Fixed.** Creates retried with the same key; one-shot reads retried; partial contention creates recorded |
| MSG-8: a stop mid-contention can let both orders reserve | Low | **Fixed** by waiting for decisions before reset |
| MSG-9: a 401/403 waits until the TTL | Low | **Fixed.** Fails fast with a plain message |
| SEC-2: the namespace could be overridden by config | Low | **Fixed.** Environment only; test override honoured only in test launch mode |
| SEC-3: the actor was the mutable username | Low | **Fixed.** Subject plus username; system rows use `system:scenario-controller` |
| SEC-4 / ARCH-9: `inventory-admin` is broader than fixtures need | Low | **Follow-up.** A fixture-only role needs an inventory-service change |
| SEC-5: 401/403 are not in the audit trail | Low | **Recorded** (architecture doc); they are in the access log |
| SEC-6: exception text leaks to callers | Low | **Fixed.** Only the service's own plain messages pass; restock null check |
| SEC-7: concurrent resets can over-stock | Low | **Fixed.** A reset without a run is serialised and refused while any run is open. Test added |
| SEC-8: unbounded DENIED rows | Low | **Follow-up** (rate limiting) |
| SEC-9 / OPS-12: the CLI exposes the token in argv; wrong client; no https check | Low | **Fixed** |
| SEC-10: the token URL scheme is not enforced | Low | **Fixed** (https, except localhost). In-cluster service calls are plain HTTP platform-wide: recorded |
| SEC-11: unbounded upstream bodies | Low | **Fixed** (1 MiB; Content-Length checked before buffering) |
| SEC-12..15: append-only triggers droppable by the owner role; readiness SQLSTATE; greetings echo; test gaps | Low/Info | Triggers: recorded (#41 pointer). Readiness and greetings: template behavior, kept. Test gaps: closed (control disabled, blank namespace, upstream allowlist) |
| PERS-4: D-008 promised a delete function | Low | **Fixed** (docs corrected) |
| PERS-7: no purge test | Info | **Fixed** |
| PERS-8: notes after RESULT | Info | **Fixed** |
| OPS-4: no traceparent from the run thread | Low | **Fixed.** A span per run. Export stays `none` platform-wide |
| OPS-5: log fields and gauge | Low | **Fixed** |
| OPS-7: runbook recovery wrong | Low | **Fixed** |
| OPS-8: no backup/restore or migration-rollback guidance | Low | **Fixed** (runbook) |
| OPS-9: GitOps env | Low | **Done** in workloads#103. `KAFKA_BOOTSTRAP_SERVERS` left in the generated ConfigMap: changing a generator literal orphans a ConfigMap (box1-docs#42 lesson) |
| OPS-10: stale README | Info | **Fixed** |
| OPS-11: reset failures not measurable | Info | **Fixed** (`scenario_resets_total{result}`) |
| ARCH-10: code and catalog fixtures could drift | Low | **Fixed** (consistency test) |
| ARCH-12: inventory create-once returns 200 for a seeded site but 409 for a seeded stock record | Low | **Recorded.** Intended: a matching site is harmless, but a stock record whose opening quantity is unknown is not; documented in inventory's runbook |
| ARCH-13: the contract lacks the new inventory routes; `ful_` naming and the held metric are uncovered by contracts | Info | **Recorded.** The patch is in `evidence/02`; the `ful_` naming is cross-checked at runtime |
