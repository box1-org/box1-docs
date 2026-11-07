# D-008 Model client, budget and concurrency

**Status:** proposed. Whether to use the endpoint before #26 secures it is a user decision (Q-3).

- **Endpoint:** `VLLM_BASE_URL=http://vllm-test-2.vllm.svc:8000/v1` (in-cluster), with `MODEL_ID=box1-coder`. The public route is never used.
- **API:** OpenAI-compatible `POST /v1/chat/completions` with a `response_format` JSON schema (guided decoding), `temperature 0`, and no `tools`. The service reads `content` only, ignores `reasoning_content`, and never returns or logs it.
- **Budget:** the server allows 98,304 tokens, but the default profile is `32k`: policy and schema ≤ 3K, evidence ≤ 16K (≈48 KiB), output `max_tokens 4096`, plus margin. `AIOPS_CONTEXT_PROFILE=16k` halves evidence and output. The service logs token counts from `usage`, never prompt text.
- **Concurrency:** one in-flight call, matching `max-num-seqs 1`, and a queue bound of 4. Beyond that, `POST` returns `429 BUSY` with `Retry-After`.
- **Timeouts:** 10s connect, 120s overall. On timeout or connection failure, the status is `MODEL_UNAVAILABLE`, with the evidence still attached and no findings.
- **Configuration:** a rest-client with a fault-tolerance timeout and no retries on POST.
- **Security:** the public route accepts anonymous calls (evidence/01). This run neither relies on nor changes it, and the finding goes to #26.
