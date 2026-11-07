# Release pass (pre-deployment)

Reviewed `fulfillment-adapter@8f576d5` (diff from `b23e7dd`) by a fresh read-only subagent given the diff, prompt, ERP1 SPEC and contracts, not the implementation reasoning. Same-model review; it does not replace human PR review. Repairs are in `11778f8`; the full suite (123 tests + 5 ITs) and the harness scenarios (50/50, TUI 6/6) were rerun afterwards.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| R1 | High | Merging fulfillment-adapter#1 now deploys a pod with no database or DLQ topic; the rollout stalls and workloads `main` points at a broken digest | **Open for the user.** The PR body says not to merge; merge order is D-009 then D-012 then the workloads PR then #1. |
| R2 | Low | The adapter API smoke had no retry for 502–504 | **Fixed.** 120 s retry. My first edit recursed, which I caught by reading it, and the extracted script passed against the local adapter. |
| R3 | Info | The release security gate has never run on this image (Camel, JSch) | **Open.** It fails closed before promotion if a CVE gate trips. |
| R4 | Medium | `earliest` on a new group may re-ingest retained `fulfillment.requested.v1` | **Open for the user.** Discovery found none were produced; recheck before enabling SFTP (D-010). |

**Verdict: not ready to merge.** It becomes conditional when the DLQ topic exists, the database and its Secret are deployed through a merged workloads PR, D-009 and D-012 are approved, and the first gated release passes the security and both smoke tasks.
