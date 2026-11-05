# Messaging pass

Reviewed commit 764ada1 in a fresh subagent, by reading only. These same-model passes do not replace human PR review or CI. Fixes landed in 078f341, retested with the full container suite.

No high findings.

| Severity | Finding | Outcome |
|---|---|---|
| Medium | Fail-fast was dead code for broker-down; a cold-start batch could take 200 s against a 60 s lease | **Fixed.** Failed futures now stop the batch. The restart test covers a cold start with the broker paused. |
| Medium | A failed dead-letter send stops the channel, fails liveness and restarts the pod | **Documented, not fixed.** No record is lost. Next action: the topic PR must merge first; no test covers this path. |
| Medium | Long database outages dead-lettered valid events | **Fixed.** See the architecture pass. |
| Low | `markPublished` failure aborted the loop | **Fixed.** Handled per row. |
| Low | Permanent publish errors retry forever | **Mitigated.** The 16K body cap removes the known trigger. Rising pending and age show the rest. Next action: classify non-retriable errors. |
| Low | `StringDeserializer` altered invalid UTF-8 in dead-letter records | **Fixed.** Byte-array value deserializer. |
| Low | The `dead_lettered` metric counts before the send is confirmed | **Accepted.** It can overcount only when the send fails, and that restarts the pod. |
| Low | Driver text reached `dead-letter-cause` | **Fixed.** See the security pass. |
