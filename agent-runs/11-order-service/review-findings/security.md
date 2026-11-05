# Security pass

Reviewed commit 764ada1 in a fresh subagent, by reading only. These same-model passes do not replace human PR review or CI. Fixes landed in 078f341, retested with the full container suite.

The missing API authentication is the user's decision, tracked in box1-docs#40, and was out of scope for findings.

| Severity | Finding | Outcome |
|---|---|---|
| High | Unbounded `customerId` and `siteId`, with a 10 MB body limit, allowed memory and disk exhaustion by unauthenticated callers | **Fixed.** Fields capped in API and contract, and body capped at 16K. Oversized body test returns 413. |
| Medium | Inbound `reasonCode` unvalidated, then stored and re-emitted | **Fixed.** Contract pattern enforced. |
| Medium | Driver text could reach logs and dead-letter headers through the exception cause | **Fixed.** Cause not chained, `logServerErrorDetail=false`, fixed-text reason, and the dead-letter test asserts no cause header. |
| Medium | Database Secret is declared inline in the workload | **Open, blocks Phase 6.** Decision D-005 and D-016. |
| Low | Event `correlationId` is free-form in MDC | **Accepted.** The contract allows it, and JSON logging escapes it in the deployed image. Escaping was not separately tested. |
| Low | NUL in `sku` | **Fixed.** |

No defects in CORS, header handling, Problem bodies, metric tags, health output, or source and fixtures. Kafka listener authentication was not probed by the reviewer; the cluster baseline records the plain listener.
