# Persistence pass (phase 5)

**Not applicable.** `agentic-operations` has no database, by the user's decision of 2026-11-06 (D-003, #97). State lives in a bounded in-memory store and the Kafka window. Their bounds, TTL from completion, eviction and restart loss are covered by the architecture pass (A-2, A-7) and the messaging pass (M-2, M-4), with tests `AnalysisStoreTest` and `EvidenceWindowTest`.
