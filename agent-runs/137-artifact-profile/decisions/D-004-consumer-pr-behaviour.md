# D-004 Consumer PR behaviour

`box1-bundle-consumer-pr` (box1-gitops `tasks/bundle-consumer-pr.yaml`):

| Situation | Behaviour |
| --- | --- |
| `gate-policy` ≠ `pass` | fails before any GitHub call |
| 0 or ≥2 `COPY --from=…/box1-ci/<repo>-bundle` lines, a tag instead of a digest, or any other reference to the bundle (FROM alias, mount) | fails naming the lines; nothing written |
| source `main` ≠ revision | outcome `superseded`; nothing written |
| consumer default branch already pins the digest | outcome `current`; an open bump PR of this automation is closed as obsolete |
| open bump PR (branch `bundle/<repo>`, body marker `box1-bundle-source: box1-org/<repo>`) proposes the same content | outcome `unchanged`; nothing written (idempotent rerun) |
| open bump PR for an older digest | branch rebuilt as one commit on the current default branch (force), PR retitled; outcome `updated` (not duplicated) |
| open PR from that branch without the marker, from a fork, or against another base | fails; nothing written |
| branch exists without an open PR | reused only if its tip is a `Bump <repo>-bundle to …` commit |
| otherwise | new PR; outcome `opened` |

Never merges. The diff is exactly one line (the digest). Tests: `test-maven-bundle.py`.
