# D-005 Random number generator and seed format

**Status:** decided by the agent, Phase 1.

- **Seed format:** a 64-bit unsigned integer shown as 16 lowercase hex characters, e.g. `5eed00000000002a`. The server generates one from `SecureRandom` when the request omits it; the page shows it and offers "replay with this seed".
- **Generator:** SplitMix64, implemented in the service (`SeededRandom`), not `java.util.Random` or `SplittableRandom`, so the sequence is fixed by our code and not by a JDK implementation detail.
- **Independent streams:** stream `i` uses seed `splitmix(seed XOR golden * (i+1))`. Stream 0 drives reading values, stream 1 the chaos schedule (interval and catalog entry), stream 2 chaos targets and parameters. Adding a chaos entry cannot shift the load values.
- **What "same sequence" means:** for the same seed and the same run configuration, the ordered list of generated readings `(index, siteId, assetId, metricName, value, unit, offsetMillis)` is identical. `offsetMillis` is the logical offset from run start, not the wall clock, so a late scheduler changes timing, never content. `measuredAt` = run start + offset (+ chaos skew where chosen).
- **Proof:** each run's audit record stores `sequenceDigest` (SHA-256 over the canonical lines of the first 200 generated readings) and the count. `GET /api/v1/control/preview` computes the first N readings for a seed and configuration without publishing anything.
