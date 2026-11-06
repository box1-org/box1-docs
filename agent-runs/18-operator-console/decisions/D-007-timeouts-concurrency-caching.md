# D-007 Timeouts, concurrency and caching per upstream

**Status:** decided.

- **Client:** Quarkus REST Client (`quarkus-rest-client-jackson`), one interface per upstream, configured by URL. Each call has a 1 s connect timeout and a 2.5 s read timeout.
- **Page budget:** an aggregate endpoint fans out in parallel on virtual threads and waits at most **3 s** in total. A source that misses the budget is reported `UNAVAILABLE` with detail `timeout after Nms`, and the response is still 200 with partial data.
- **Bulkhead:** at most 8 in-flight calls per upstream (semaphore). An excess call fails fast as `DEGRADED` "busy" and does not queue.
- **Retries:** none. Retrying a read inside a 3 s budget only adds load, and the user can reload.
- **Caching:** only `/api/info` revisions, for 60 s. Business state is never cached, so the UI never shows stale state as current.
- **Order list window** (D-013): at most 2 order-service pages of 100.
