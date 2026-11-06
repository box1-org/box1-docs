# Release pass

**Not run.** The profile's Release pass checks that the digest matches the GitOps promotion, Argo reports the expected revision, the running pod uses that digest, and endpoints and OpenAPI examples work. Nothing has been merged or deployed, so there is nothing to review. It runs after Phase 6 delivery, in a fresh subagent, against the observed release.
